import keyboard

def run_buzzer_simulator(callback, stop_event):
      is_on = False
      def on_press(e):
            nonlocal is_on
            if is_on == False:
                  callback(True)
                  is_on = True

      def on_release(e):
            nonlocal is_on
            if is_on == True:
                  callback(False)
                  is_on = False

      h1 = keyboard.on_press_key('2', on_press)
      h2 = keyboard.on_release_key('2', on_release)
      stop_event.wait()
      keyboard.unhook(h1)
      keyboard.unhook(h2)