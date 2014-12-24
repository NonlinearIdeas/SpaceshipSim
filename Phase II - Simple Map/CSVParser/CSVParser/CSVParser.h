//
//  CSVParser.h
//  CSVParser
//
//  Created by James Wucher on 12/23/14.
//  Copyright (c) 2014 James Wucher. All rights reserved.
//

#ifndef __CSVParser__
#define __CSVParser__

#include <stdio.h>

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <sstream>
#include <istream>

using namespace std;

class CSVParser
{
private:
   const vector<string> csv_read_row(istream &in, char delimiter)
   {
      stringstream ss;
      bool inquotes = false;
      vector<string> row;//relying on RVO
      while(in.good())
      {
         char c = in.get();
         if (!inquotes && c=='"') //beginquotechar
         {
            inquotes=true;
         }
         else if (inquotes && c=='"') //quotechar
         {
            if ( in.peek() == '"')//2 consecutive quotes resolve to 1
            {
               in.get();
               ss << "\"";
            }
            else //endquotechar
            {
               inquotes=false;
            }
         }
         else if (!inquotes && c==delimiter) //end of field
         {
            row.push_back( ss.str() );
            ss.str("");
         }
         else if(!inquotes && c == '\r')
         {  // Throw away a \r.
            continue;
         }
         else if (!inquotes && c=='\n')
         {
            row.push_back( ss.str() );
            return row;
         }
         else
         {
            ss << c;
         }
      }
      return row;
   }
   
   const vector<string> csv_read_row(string &line, char delimiter)
   {
      stringstream ss(line);
      return csv_read_row(ss, delimiter);
   }
   
   vector< vector<string> > _result;

public:
   
   const vector< vector<string> >& Parse(const string& fileName, char delimiter = ',')
   {
      _result.clear();
      ifstream in(fileName, std::ifstream::in | std::ifstream::binary);
      if (in.good())
      {
         while(in.good())
         {
            const vector<string> row = csv_read_row(in,delimiter);
            if(row.size() > 0)
            {
               _result.push_back(row);
            }
         }
      }
      in.close();
      return _result;
   }
};

#endif /* defined(__CSVParser__) */
