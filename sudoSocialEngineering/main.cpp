#include <cstdlib>
#include <iostream>
#include <print>
#include <string>
#include <sys/types.h>
#include <termios.h>
#include <unistd.h>

void setStdinEcho(bool /*enable*/);
auto getUserName() -> std::string;


void setStdinEcho(bool enable)
{
    struct termios tty
    {};
    tcgetattr(STDIN_FILENO, &tty);
    if (!enable)
    {
        tty.c_lflag &= static_cast<unsigned int>(~ECHO);
    }
    else
    {
        tty.c_lflag |= ECHO;
    }

    (void)tcsetattr(STDIN_FILENO, TCSANOW, &tty);
}


auto getUserName() -> std::string
{
    //NOLINTNEXTLINE(concurrency-mt-unsafe)
    return getenv("SUDO_USER");
}

auto main([[maybe_unused]] int argc, char** argv) -> int
{
    // Check if run with sudo
    if (geteuid() != 0)
    {
        std::print("This program must be run with sudo\n");
        return 1;
    }

    const std::string USER_NAME = getUserName();
    std::print("Sorry, try again.\n[sudo] password for {}: ", USER_NAME);

    std::string input {};

    setStdinEcho(false);
    std::getline(std::cin, input, '\n');
    setStdinEcho(true);

    std::print("\nThank you for your password. \"{}:{}\"\n", USER_NAME, input);

    const int EXIT_SIGSEGV {11};
    return EXIT_SIGSEGV;
}
