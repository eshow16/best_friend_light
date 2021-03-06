import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library

from repositories.ColorRepository import ColorRepository
from threading import Thread
import time

# run the best friend light program
class BestFriendLight(object):

  # led_controller to light up the leds
  _led_controller = None

  # the colors to choose from to light up
  _colors = []

  # the current color we are on within the above color array
  _color_index = 0

  # the pin that we will use to read the push button
  _push_button_pin = 0

  # the last state of the push button pin
  _last_state = GPIO.HIGH

  # the repository used to change and retrieve the latest color
  _color_repository = None

  # whether or not we are actively requesting a color
  _currently_requesting_color = False

  def __init__(self, led_controller, colors, push_button_pin):
    super(object, self).__init__()
    self._led_controller = led_controller
    self._colors = colors
    self._push_button_pin = push_button_pin
    self._color_repository = ColorRepository()

    # setup the push button gpio input
    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
    GPIO.setup(self._push_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin to be an input pin and set initial value to be pulled low (off)


  def run(self):
    while True:
      # first check if the user pressed the button
      self.check_for_user_input()
      # then check if the other person changed the color
      if not self._currently_requesting_color:
        # open this in a new thread so we don't block the push button check
        self._currently_requesting_color = True
        thread = Thread(target = self.check_for_new_color)
        thread.start()

  def check_for_new_color(self):
    current_color_index = self._color_repository.get_current_color(self._color_index)

    if current_color_index != self._color_index:
      # set to the color index right before the current color index, so when we switch colors,
      # we light up the correct color. protect against invalid color indexes
      self._color_index = (current_color_index + len(self._colors) - 1) % len(self._colors)
      self.switch_to_next_color()

    # wait 5 seconds between requests
    time.sleep(5)
    self._currently_requesting_color = False

  def check_for_user_input(self):
    # first check if we changed the color
    switched_high = GPIO.input(self._push_button_pin) == GPIO.HIGH and self._last_state != GPIO.HIGH
    switched_low = GPIO.input(self._push_button_pin) == GPIO.LOW and self._last_state != GPIO.LOW

    # as long as we pressed the button, change the color
    if switched_low or switched_high:
      self.switch_to_next_color()
      self._color_repository.set_current_color(self._color_index)

    self._last_state = GPIO.input(self._push_button_pin)

  def switch_to_next_color(self):
    self._color_index = (self._color_index + 1) % len(self._colors)
    self._led_controller.turn_on_color(self._colors[self._color_index])