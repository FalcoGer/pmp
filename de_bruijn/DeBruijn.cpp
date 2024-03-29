#include "DeBruijn.h"
#include <sstream>
#include <algorithm>
#include <cmath>
#include <iostream>

/// Initialize DeBruijn sequence with hex digits as alphabet
DeBruijn::DeBruijn()
{
  for (auto c : "0123456789ABCDEF")
  {
    [[likely]]
    if (c) // skip null byte
    {
      this->alphabet.push_back(static_cast<uint8_t>(c));
    }
  }
  k = this->alphabet.size();
}

/// Initialize DeBruijn sequence
/// \param alphabet The alphabet to use
DeBruijn::DeBruijn(std::vector<uint8_t> alphabet)
{
  for (uint8_t c : alphabet)
  {
    // exclude duplicates
    if (std::find(this->alphabet.begin(), this->alphabet.end(), c) == this->alphabet.end())
    {
      this->alphabet.push_back(c);
    }
  }
  k = this->alphabet.size();
}

/// Initialize DeBruijn sequence
/// \param alphabet The alphabet to use
DeBruijn::DeBruijn(std::string_view alphabet)
{
  for (char c : alphabet)
  {
    // exclude duplicates
    if (std::find(this->alphabet.begin(), this->alphabet.end(), c) == this->alphabet.end())
    {
      this->alphabet.push_back(static_cast<uint8_t>(c));
    }
  }
  k = this->alphabet.size();
}

double DeBruijn::len(unsigned int n)
{
  return std::pow(k, n);
}

std::string DeBruijn::returnSequence(unsigned int n)
{
  this->cb = &DeBruijn::cb_add2seq;

  this->generate(n);

  // turn sequence into string
  std::stringstream ss;
  for (auto idx : sequence)
  {
    ss << alphabet[idx];
  }
  
  return ss.str();
}

void DeBruijn::printSequence(unsigned int n)
{
  this->cb = &DeBruijn::cb_print;
  this->generate(n);
  return;
}


/// Generate De Bruijn sequence. Ref: https://en.wikipedia.org/wiki/De_Bruijn_sequence#Example_using_de_Bruijn_graph
/// \param n Length of the sequence
/// \return The sequence.
void DeBruijn::generate(unsigned int n)
{
  this->n = n;
  this->sequence.clear();
  this->a.clear();
  for (size_t i = 0; i < n*k; i++)
  {
    this->a.push_back(0u);
  }

  // FIXME: un-recurse!
  // generate sequence using a recursive function (bleh!)
  db(1u,1u);
  return;
}

void DeBruijn::db(unsigned int t, unsigned int p)
{
  if (t > n)
  {
    if (n % p == 0)
    {
      // sequence.extend(a[1 : p + 1])
      for (size_t idx = 1; idx <= p; idx++)
      {
        std::invoke(cb, *this, idx);
        // this->sequence.push_back(a[idx]);
      }
    }
  }
  else
  {
    a[t] = a[t - p];
    db(t + 1, p);
    // for j in range(a[t - p] + 1, k):
    for (unsigned int j = a[t-p] + 1; j < k; j++)
    {
      a[t] = j;
      db(t + 1, t);
    }
  }
}

void DeBruijn::cb_print(unsigned int idx)
{
    std::cout << alphabet[a[idx]];
}

void DeBruijn::cb_add2seq(unsigned int idx)
{
    sequence.push_back(a[idx]);
}
