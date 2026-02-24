"""*FlowTimer, but Pomodoro cuz I'm ADHD*."""

import sys
from datetime import timedelta
from time import sleep
from typing import ClassVar, NoReturn

playsound_lib_installed: bool = True

try:
    from playsound3 import playsound
except ImportError:
    playsound_lib_installed = False

type Second = int
type StringLength = int


class _State:
    # Used for development
    debug: bool = False
    commands_completed: bool = False
    statistics_completed: bool = False

    # Used in the actual program
    max_len: StringLength = 0
    focus_topics: ClassVar[dict[int, tuple[str, Second]]] = {}
    focus_sec: Second = 0
    break_sec: Second = 0
    focus_sessions: int = 0
    break_sessions: int = 0
    focus_total: Second = 0
    break_total: Second = 0
    top_line: str
    bottom_line: str


_self: _State = _State()


def _alarm() -> None:
    if playsound_lib_installed:
        playsound("./breakalarm.wav")


def _box_newline(string: str = "") -> None:
    print("\u2503 " + (" " * _self.max_len) + " \u2503" + string)


def _box_line(string: str) -> None:
    _box_newline("\033[3G" + string)


def _error_box(string: str) -> None:
    print("\n" + _self.top_line)
    _box_line(string)
    print(_self.bottom_line + "\033[5A")
    _box_line("> ")
    print("\033[1A" + "\033[5G", end="")


def _input_box(message: str, *, timer: bool, one_arg: bool = False) -> None:
    if not one_arg:
        print()
    print(_self.top_line)
    _box_line(message)
    _box_line("" if timer else "> ")
    print(
        _self.bottom_line + "\033[1A" + ("\033[3G" if timer else "\033[5G"),
        end="",
    )


def _timer(seconds: Second) -> None:
    secs: Second = seconds  # haha, it sounds like funny word
    timer: timedelta = timedelta(seconds=secs)
    while secs > -1:
        timer = timedelta(seconds=secs)
        print(timer, end="\r\033[2C")
        sleep(1)
        secs -= 1


def _before_input_box_print(args: tuple[str, ...]) -> None:
    for arg in args[:-1]:
        if "[newline]" in arg:
            _box_newline()
            _box_line(arg.replace("[newline]", ""))
        elif "[placeholder]" in arg:
            continue
        else:
            _box_line(arg)


def _pprint(*args: str, seconds: Second | None = None) -> None:
    _self.max_len: StringLength = len(max(args, key=len))
    line: str = "\u2501" * (_self.max_len + 2)
    _self.top_line: str = "\u250f" + line + "\u2513"
    _self.bottom_line: str = "\u2517" + line + "\u251b"
    print("\033[H" + "\033[2J", end="")
    length: int = len(args)
    if length > 1:
        print(_self.top_line)
        _before_input_box_print(args)
        print(_self.bottom_line)
    _input_box(
        args[-1],
        timer=bool(seconds),
        one_arg=bool(length == 1),
    )
    if seconds:
        _timer(seconds)


def _y_or_n_match(init_input: str) -> bool:
    uinput: str = init_input
    while True:
        match uinput:
            case "y":
                return True
            case "N":
                return False
            case "_":
                _error_box('Input "y" for "yes" and "N" for "no".')
                uinput: str = input()


def _exit_pmdr() -> NoReturn:
    print("\033[H" + "\033[2J", end="")
    sys.exit("Successfully exited pmdr.")


def _uinput() -> str:
    uinput: str = input()

    # The commands are a WIP.
    match uinput:
        case "-h" | "--help":
            return uinput

            # WIP
            _pprint(
                "General INFO:",
                "  pmdr is a (somewhat) customizable pomodoro timer REPL.",
                "  The program cycles between focus sessions and breaks.",
                "  You can set how long you focus for.",
                "  The default is 25 minutes.",
                "  Then, a break is given.",
                "  Break.",
                "  As is pomodoro tradition, on every fourth break, "
                "the time will be tripled.",
                "[newline]Commands:",
                "  -h, --help             : Brings up this menu",
                "  -e, --exit             : Immediately exits the program",
                "  --stats, --statistics  : Displays total statistics",
                "Press ENTER to return.",
            )
        case "-e" | "--exit":
            _exit_pmdr()
        case "--statistics":
            pass
        case "_":
            pass

    return uinput


def _time_format(*, seconds: Second) -> str:
    hours: int = seconds // 3600
    minutes: int = (seconds // 60) % 60
    sec: Second = seconds % 60

    return f"{hours}h, {minutes}m, {sec}s"


def _y_or_n() -> bool:
    while True:
        user_input: str = _uinput()
        if user_input == "y":
            return True
        if user_input == "N":
            return False
        _error_box('Input "y" for "yes" and "N" for "no".')


DEBUG_FOCUS_SEC: Second = 5
DEFAULT_FOCUS_SEC: Second = 1500


def _focus_minutes_input() -> None:
    while True:
        uinput: str = _uinput()
        if _self.debug:
            break
        if not uinput.isnumeric():
            _error_box('Input a positive integer, like "15" or "20".')
            continue
        focus_minutes: int = int(uinput)
        if focus_minutes == 0:
            _error_box("Input a value greater than zero.")
            continue
        break
    if focus_minutes:
        _self.focus_sec: Second = focus_minutes * 60
    elif _self.debug:
        _self.focus_sec: Second = DEBUG_FOCUS_SEC
    else:
        _self.focus_sec: Second = DEFAULT_FOCUS_SEC


def _focus() -> bool:
    if _self.focus_sessions > 0:
        _pprint("Would you like to start another focus session? (y/N)")
        if not _y_or_n():
            return False
    _self.focus_sessions += 1
    _pprint(
        "What will you be working on during this focus session?",
        "I'll be working on...",
    )
    focus_topic: str = _uinput()
    _pprint(
        "How many MINUTES would you like to work for?",
        "[newline]Press ENTER for the default value of 25 MINUTES.",
        "Minutes:",
    )
    _focus_minutes_input()
    _pprint(
        f"Focus Session #{_self.focus_sessions} has STARTED!",
        "[newline]Your current focus is on:",
        f"{focus_topic}",
        "Focus time left:",
        seconds=_self.focus_sec,
    )
    _alarm()
    _self.focus_total += _self.focus_sec
    _self.focus_topics[_self.focus_sessions] = (
        focus_topic,
        _self.focus_sec,
    )
    return True


def _break() -> bool:
    total: str = _time_format(seconds=_self.focus_total)
    _pprint(
        f"Focus Session #{_self.focus_sessions} has ENDED!",
        "[newline]TOTAL time spent in focus sessions:",
        total,
        "Would you like to take a break? (y/N)",
    )
    if not _y_or_n():
        return False
    if _self.focus_sessions == 1:
        _pprint(
            "Break Session INFO:",
            "  Your break time is automatically ONE FIFTH of your focus time.",
            "  And it TRIPLES every FOUR focus sessions!",
            "Press ENTER when you are done reading.",
        )
        _uinput()
    _self.break_sessions += 1
    _self.break_sec: int = _self.focus_sec // 5
    four_breaks_in: bool = _self.break_sessions % 4 == 0
    if four_breaks_in:
        _self.break_sec *= 3
    _pprint(
        f"Break #{_self.break_sessions} has STARTED!",
        "Your break time has been TRIPLED."
        if four_breaks_in
        else "[placeholder]",
        "Break time left:",
        seconds=_self.break_sec,
    )
    _alarm()
    _self.break_total += _self.break_sec
    return True


def _statistics() -> None:
    _pprint("TOTAL Stats:\n")
    for i in range(1, len(_self.focus_topics) + 1):
        info: tuple[str, Second] = _self.focus_topics[i]
        topic: str = info[0]
        mins: str = _time_format(seconds=info[1])
        print(f"Session #{i}:")
        print(f"Worked on {topic} for {mins}.\n")
    bfc: str = _time_format(seconds=_self.break_total)
    bs: str = "s" if _self.break_sessions > 1 else ""
    print(f"And you spent {bfc} over {_self.break_sessions} break{bs}.\n")


def main() -> None:
    """*Run `pmdr`*."""
    _pprint(
        "Welcome to pmdr!",
        'Type "-h" or "--help" at anytime for more info.'
        if _self.commands_completed
        else 'Type "-e" or "--exit" at anytime to exit the program.',
        "Would you like to start a focus session? (y/N)",
    )
    if not _y_or_n():
        _exit_pmdr()
    while True:
        if not _focus():
            break
        if not _break():
            break
    if _self.statistics_completed:
        _statistics()
    print("Press ENTER to exit pmdr.")
    input()


if __name__ == "__main__":
    main()
