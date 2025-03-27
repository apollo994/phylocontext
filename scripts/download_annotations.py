#!/usr/bin/env python3

import argparse

def main():

    parser = argparse.ArgumentParser(description='My nice tool')
    parser.add_argument('--input', help='')
    args = parser.parse_args()



if __name__ == "__main__":
    main()
