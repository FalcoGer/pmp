#include <iostream>
#include <sstream>
#include "DeBruijn.h"

int main(int argc, char** argv)
{
    if (argc == 1 || argc > 3)
    {
        std::cout << "Usage: " << argv[0] << " <len> [alphabet]\n" 
            << "    If alphabet is not provided, the hex digits will be used." << std::endl;
        return 0;
    }
    DeBruijn* sequence = nullptr;
    if (argc == 2)
    {
        sequence = new DeBruijn();
    }
    else if (argc == 3)
    {
        sequence = new DeBruijn(argv[2]);
    }
    else
    {
        return -1; // shouldn't happen
    }

    unsigned int len = 0;
    std::stringstream ss;
    ss << argv[1];
    ss >> len;

    if (ss.fail())
    {
        std::cout << "Couldn't convert \"" << argv[1] << "\" into a number." << std::endl;
        return -1;
    }
    
    double resultLen = sequence->len(len);
    if (resultLen > 1e+9)
    {
        std::cerr << "Resulting string is " << resultLen << " Bytes long. This may break." << std::endl;
    }
    // std::cout << sequence->returnSequence(len) << std::endl;
    sequence->printSequence(len);

    delete sequence;
    sequence = nullptr;

    return 0;
}
