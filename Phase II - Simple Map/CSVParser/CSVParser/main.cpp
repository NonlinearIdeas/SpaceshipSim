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


#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <sstream>
#include <istream>

using std::cout;
using std::endl;

std::vector<std::string> csv_read_row(std::istream &in, char delimiter = ',');
std::vector<std::string> csv_read_row(std::string &in, char delimiter = ',');

int main(int argc, char *argv[])
{
   std::ifstream in("input.csv", std::ifstream::in | std::ifstream::binary);
   if (in.fail()) return (cout << "File not found" << endl) && 0;
   while(in.good())
   {
      std::vector<std::string> row = csv_read_row(in);
      for(unsigned int idx = 0; idx < row.size(); idx++)
      {
         cout << "[" << row[idx] << "]" << "\t";
      }
      cout << endl;
   }
   in.close();
   
   /*
   std::string line;
   in.open("input.csv");
   while(getline(in, line)  && in.good())
   {
      std::vector<std::string> row = csv_read_row(line, ',');
      for(int i=0, leng=row.size(); i<leng; i++)
         cout << "[" << row[i] << "]" << "\t";
      cout << endl;
   }
   in.close();
   */
   
   return 0;
}

std::vector<std::string> csv_read_row(std::string &line, char delimiter)
{
   std::stringstream ss(line);
   return csv_read_row(ss, delimiter);
}

std::vector<std::string> csv_read_row(std::istream &in, char delimiter)
{
   std::stringstream ss;
   bool inquotes = false;
   std::vector<std::string> row;//relying on RVO
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
