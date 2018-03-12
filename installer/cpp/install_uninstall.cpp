#include "stdafx.h"
#include <fstream>
#include <iostream>
#include <string>
using namespace std;

void write_error(string msg);
const bool mode_uninstall = false;

int main()
{
    // read windir from env
    string windir = getenv("windir");
    string hosts_file_name = windir + "\\System32\\drivers\\etc\\hosts";

    // confirm user wants to continue
    if (mode_uninstall) {
        cout << "This program will modify " << hosts_file_name << ". You will no longer be able to connect to LocalSO." << endl << "A backup will be created." << endl << endl;
    } else {
        cout << "This program will modify " << hosts_file_name << " so that you can connect to LocalSO." << endl << "A backup will be created." << endl << endl;
    }
    cout << "Do you want to continue? [Y/N]? ";
    string answer;
    cin >> answer;
    if (answer.compare("y")!=0 && answer.compare("Y")!=0) {
        system("pause");
        return 0;
    }

    // open the hosts file
    ifstream hosts_file(hosts_file_name);
    if (!hosts_file) {
        write_error("ERROR! Failed to open " + hosts_file_name);
        return 1;
    }

    // count number of lines
    int num_lines = 0;
    string str;
    while (getline(hosts_file, str)) {
        num_lines++;
    }

    // rewind the ifstream
    hosts_file.clear();
    hosts_file.seekg(0);

    // read lines into array and close file
    string* lines = new string[num_lines];
    num_lines = 0;
    while(getline(hosts_file, str)) {
        lines[num_lines++] = str;
    }
    hosts_file.close();

    // open backup ofstream
    cout << endl << "Writing backup file " << hosts_file_name << ".bak" << endl;
    ofstream hosts_file_backup(hosts_file_name + ".bak");
    if (!hosts_file_backup) {
        write_error("ERROR! Failed to write backup file!");
        return 1;
    }

    // write backup file
    for (int i = 0; i < num_lines; i++) {
        hosts_file_backup << lines[i] << endl;
    }
    hosts_file_backup.close();

    // open hosts file
    ofstream hosts_file_new(hosts_file_name);
    if (!hosts_file_backup) {
        write_error("ERROR! Failed to write to hosts file!");
        return 1;
    }

    // write to hosts file
    for (int i = 0; i < num_lines; i++) {
        string line = lines[i];
        if (line.find("stickonline.redirectme.net") == string::npos && line.find("stick-online.com") == string::npos) {
            hosts_file_new << line << endl;
        }
    }

    // write new entries
    if (mode_uninstall) {
        cout << "Removing 127.0.0.1 stick-online.com" << endl;
        cout << "Removing 127.0.0.1 www.stick-online.com" << endl;
        cout << "Removing 127.0.0.1 stickonline.redirectme.net" << endl;
    } else {
        cout << "Adding 127.0.0.1 stick-online.com" << endl;
        hosts_file_new << endl; // prepend a newline just incase
        hosts_file_new << "127.0.0.1 stick-online.com" << endl;
        cout << "Adding 127.0.0.1 www.stick-online.com" << endl;
        hosts_file_new << "127.0.0.1 www.stick-online.com" << endl;
        cout << "Adding 127.0.0.1 stickonline.redirectme.net" << endl;
        hosts_file_new << "127.0.0.1 stickonline.redirectme.net" << endl;
    }

    // close hosts file
    hosts_file_new.close();

    cout << "Done!";
    if (!mode_uninstall) {
        cout << " You can now launch StickOnline.exe";
    }
    cout << endl << endl;
    system("pause");
}

void write_error(string msg) {
    cout << msg << endl << "Are you running as administrator?" << endl;
    system("pause");
    exit(1);
}
