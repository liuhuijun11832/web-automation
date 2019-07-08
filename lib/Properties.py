# -*-encoding: utf-8 -*-
import re


class Properties(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.properties = {}
        try:
            with open(file_name, 'r', encoding='utf-8') as fp:
                for line in fp:
                    line = line.strip()
                    line = re.sub(r'\s+=\s+', '$equals$', line)
                    if line.find('=') > 0 and not line.startswith('#'):
                        strs = line.split('=')
                        self.properties[strs[0].strip()] = strs[1].strip()
        except Exception as e:
            raise e

    def contains(self, key):
        return key in self.properties

    def get(self, key, default=''):
        if key in self.properties:
            return self.properties[key]
        return default

    def put(self, key, value):
        self.properties[key] = value


def parse(file_name):
    return Properties(file_name)
