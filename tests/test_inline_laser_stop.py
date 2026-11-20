"""Execute production ISR helpers and quick-stop ordering against fake hardware.

This is a host regression harness, not an MCU/timing or full stepper simulation.
It extracts complete function bodies verbatim to avoid copying their logic.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def function(path, signature):
    text = (ROOT / path).read_text()
    start = text.index(signature)
    brace = text.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


class InlineLaserStopTest(unittest.TestCase):
    def test_output_release_resume_focus_and_quickstop(self):
        production = '\n'.join([
            function('snapmaker/src/module/toolhead_laser.cpp', 'bool ToolHeadLaser::SetAirPumpSwitch('),
            function('snapmaker/src/module/toolhead_laser.cpp', 'void ToolHeadLaser::BlankOutput_ISR()'),
            function('snapmaker/src/module/toolhead_laser.cpp', 'void ToolHeadLaser::TurnOn_ISR('),
            function('Marlin/src/module/stepper.cpp', 'void Stepper::finish_inline_laser_block('),
            function('Marlin/src/module/planner.cpp', 'void Planner::quick_stop()'),
            function('Marlin/src/Marlin.cpp', 'static void blank_laser_before_kill()'),
        ])
        setup = r'''
#include <cassert>
#include <cstdint>
#define ENABLED(x) 0
#define LOG_I(...) ((void)0)
#define TERN_(...) 
constexpr int BLOCK_DELAY_FOR_1ST_MOVE = 100;
enum State { TOOLHEAD_LASER_STATE_OFFLINE, TOOLHEAD_LASER_STATE_OFF, TOOLHEAD_LASER_STATE_ON };
uint16_t physical_pwm = 0;
unsigned writes = 0;
void TimSetPwm(uint16_t p) { physical_pwm = p; ++writes; }
struct ToolHeadLaser {
  State state_ = TOOLHEAD_LASER_STATE_OFF;
  uint16_t power_pwm_ = 137, power_limit_pwm_ = 255;
  float power_val_ = 53.0f;
  bool inline_enabled = true;
  volatile bool air_pump_switch_ = false, air_pump_suspended_ = false;
  bool SetAirPumpSwitch(bool, bool = true);
  GET_PUMP_OUTPUT
  GET_PUMP_REQUEST
  void BlankOutput_ISR();
  void TurnOn_ISR(uint16_t, bool, float);
  void InlineDisable() { inline_enabled = false; }
};
ToolHeadLaser head;
ToolHeadLaser *laser = &head;
struct Block { struct { struct { bool isEnabled; } status; } laser; };
struct Stepper {
  static Block *current_block;
  static bool aborted;
  static void finish_inline_laser_block(bool);
  static void quick_stop() { aborted = true; }
} stepper;
Block *Stepper::current_block = nullptr;
bool Stepper::aborted = false;
struct Planner {
  int block_buffer_nonbusy = 4, block_buffer_planned = 5;
  int block_buffer_head = 6, block_buffer_tail = 2;
  int delay_before_delivering = 0, cleaning_buffer_counter = 0;
  void quick_stop();
};
bool irq_enabled = true;
unsigned reenables = 0;
#define STEPPER_ISR_ENABLED() irq_enabled
#define DISABLE_STEPPER_DRIVER_INTERRUPT() (irq_enabled = false)
void reenable() {
  // These conditions must already hold when the ISR can run again.
  assert(physical_pwm == 0);
  assert(Stepper::aborted);
  assert(!laser->inline_enabled);
  irq_enabled = true;
  ++reenables;
}
#define ENABLE_STEPPER_DRIVER_INTERRUPT() reenable()
'''
        setup = setup.replace('GET_PUMP_OUTPUT', function(
            'snapmaker/src/module/toolhead_laser.h', 'bool GetAirPumpOutput(void)'))
        setup = setup.replace('GET_PUMP_REQUEST', function(
            'snapmaker/src/module/toolhead_laser.h', 'bool GetAirPumpSwitch(void)'))
        scenarios = r'''
int main() {
  // The production blanking path is common to every head, including 2 W IR.
  for (int device = 0; device < 5; ++device) {
    head = ToolHeadLaser();
    head.TurnOn_ISR(137, true, 53.0f);
    Stepper::current_block = nullptr;
    Stepper::finish_inline_laser_block(true);
    assert(physical_pwm == 0 && head.state_ == TOOLHEAD_LASER_STATE_OFF);
    assert(head.power_pwm_ == 137 && head.power_val_ == 53.0f);
    assert(head.inline_enabled); // Pause/underrun does not erase modal power.

    // A later movement (resume) owns its output and restores its own power.
    Block next{{{true}}};
    Stepper::current_block = &next;
    head.TurnOn_ISR(91, true, 35.0f);
    const auto before = writes;
    Stepper::finish_inline_laser_block(true);
    assert(physical_pwm == 91 && writes == before); // No inter-block off pulse.

    // Transition to a non-inline block must not inherit previous inline PWM.
    next.laser.status.isEnabled = false;
    Stepper::finish_inline_laser_block(true);
    assert(physical_pwm == 0);

    // After an inline move ends, explicitly requested stationary focus persists.
    Stepper::current_block = nullptr;
    physical_pwm = 3;
    head.state_ = TOOLHEAD_LASER_STATE_ON;
    for (int idle_tick = 0; idle_tick < 100; ++idle_tick)
      Stepper::finish_inline_laser_block(false);
    assert(physical_pwm == 3);

    // An explicit quick stop blanks even direct focus output; no CAN calls.
    Planner p;
    Stepper::aborted = false;
    irq_enabled = true;
    head.inline_enabled = true;
    p.quick_stop();
    assert(p.block_buffer_head == p.block_buffer_tail);
    assert(p.block_buffer_nonbusy == p.block_buffer_tail);
    assert(p.block_buffer_planned == p.block_buffer_tail);
    assert(p.cleaning_buffer_counter == 1000);
    assert(physical_pwm == 0 && irq_enabled);

    // Do not enable a stepper IRQ that the caller already disabled.
    irq_enabled = false;
    const auto old_reenables = reenables;
    p.quick_stop();
    assert(!irq_enabled && reenables == old_reenables);
  }
  // Layer request survives a drained-stream pause, physical output does not.
  head = ToolHeadLaser();
  head.SetAirPumpSwitch(true);
  assert(head.GetAirPumpOutput()); // Manual M7/M8 still works immediately.
  head.TurnOn_ISR(100, true, 40.0f);
  Stepper::current_block = nullptr;
  Stepper::finish_inline_laser_block(true);
  assert(head.GetAirPumpSwitch() && !head.GetAirPumpOutput());
  head.BlankOutput_ISR();
  assert(head.GetAirPumpSwitch() && !head.GetAirPumpOutput());
  head.TurnOn_ISR(0, true, 0.0f); // Resume with a zero-power raster segment.
  assert(head.GetAirPumpOutput());

  // M9 while paused must prevent pump restart on resume.
  head.BlankOutput_ISR();
  head.SetAirPumpSwitch(false);
  head.TurnOn_ISR(100, true, 40.0f);
  assert(!head.GetAirPumpSwitch() && !head.GetAirPumpOutput());

  // Explicit M7 overrides suspension; explicit quick-stop cancels the request.
  head.BlankOutput_ISR();
  head.SetAirPumpSwitch(true);
  assert(head.GetAirPumpOutput());
  Planner stopped;
  irq_enabled = true;
  stopped.quick_stop();
  assert(!head.GetAirPumpSwitch() && !head.GetAirPumpOutput());
  head.TurnOn_ISR(100, true, 40.0f);
  assert(!head.GetAirPumpOutput());

  // M112/kill must blank before interrupt shutdown / diagnostic delays.
  head.state_ = TOOLHEAD_LASER_STATE_ON;
  physical_pwm = 200;
  irq_enabled = true;
  head.inline_enabled = true;
  blank_laser_before_kill();
  assert(!irq_enabled && physical_pwm == 0 && !head.inline_enabled);

  // Offline laser objects must not touch the uninitialized PWM hardware.
  head.state_ = TOOLHEAD_LASER_STATE_OFFLINE;
  const auto old_writes = writes;
  head.BlankOutput_ISR();
  assert(writes == old_writes);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'inline_stop.cpp'
            binary = Path(tmp) / 'inline_stop'
            src.write_text(setup + production + scenarios)
            subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++11', '-Wall',
                            '-Wextra', '-Werror', str(src), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
