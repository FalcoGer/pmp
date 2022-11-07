#pragma once

#include <set>
#include <string_view>
#include <string>
#include <vector>

class DeBruijn
{
  public:
    DeBruijn();
    DeBruijn(std::vector<uint8_t> alphabet);
    DeBruijn(std::string_view alphabet);
    ~DeBruijn() = default;
    std::string generate(unsigned int n);
    double len(unsigned int n);
  private:
    void db(unsigned int t, unsigned int p);
    
    // the alphabet that is used
    std::vector<uint8_t> alphabet;
    
    // the sequence of indexes in the alphabet that is generated
    std::vector<unsigned int> sequence;
    std::vector<unsigned int> a;
    
    // the size of the alphabet
    size_t k;
    
    // the length of the requested string to be included
    unsigned int n;
};
