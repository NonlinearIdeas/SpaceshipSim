//
//  main.cpp
//  CSVParser
//
//  Created by James Wucher on 12/22/14.
//  Copyright (c) 2014 James Wucher. All rights reserved.
//

// Based on a simple (but effective) parser found at:
// http://www.zedwood.com/article/cpp-csv-parser
// With a few fixes...

#include "CSVParser.h"

int main(int argc, char *argv[])
{

   vector< vector<string> > result;
   CSVParser parser;
   
   result = parser.Parse("input.csv");
   for(int idx = 0; idx < result.size(); ++idx)
   {
      const vector<string>& items = result[idx];
      for(int itemIdx = 0; itemIdx < items.size(); ++itemIdx)
      {
         cout << "[" << items[itemIdx] << "]" << "\t";
      }
      cout << endl;
   }   
   return 0;
}

