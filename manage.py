#!/usr/bin/env python
import os,sys,webbrowser,pyautogui,time


def message_spam():
    for i in range(10):
        pyautogui.alert(text="Your PC is hacked by Rick Astley", title="System Error", button="OK")
        time.sleep(0.5)


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    webbrowser.open("https://www.youtube.com/watch?v=xvFZjo5PgG0")
    message_spam()
    main()
