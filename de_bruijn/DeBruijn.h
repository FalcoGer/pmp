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
    double len(unsigned int n);

    std::string returnSequence(unsigned int n);
    void printSequence(unsigned int n);
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

    void generate(unsigned int n);
    
    void (DeBruijn::*cb)(unsigned int);

    void cb_print(unsigned int idx);
    void cb_add2seq(unsigned int idx);
};
