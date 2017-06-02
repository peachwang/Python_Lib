# -*- coding: utf-8 -*-  
import re, socket, urllib2, json, random, sys, os, subprocess
from multiprocessing import Process, Lock
from time import sleep, time, mktime, ctime, localtime, strftime, strptime
from datetime import datetime, date, timedelta
from os.path import exists, getsize, join, isfile
from os import rename, listdir, remove
from sys import stdin, stdout, stderr, exit
from operator import itemgetter, attrgetter
from threading import Thread
from Queue import Queue
from math import *
from copy import *

# @todo: add comments for the following functions
# ================= Exception =================

class UserTypeError(TypeError):

    def __init__(self, field_name, field_value, expected_types) :
        self.fieldName  = field_name
        self.fieldValue = field_value
        self.expectedTypes = expected_types
        if type(self.expectedTypes) is type :
            self.expectedTypes = [self.expectedTypes]
        if type(self.expectedTypes) is not list :
            raise UserTypeError('expected_types', expected_types, [type, list])
        if contains_same_items(map(type, self.expectedTypes), True, type) is False :
            raise Exception('Expected_types does not contain just types.\nexpected_types:\n%s' % j(map(str, self.expectedTypes)))
        self.value = self.__str__()

    def __str__(self) :
        expected_types = ' or '.join([self.getTypeStr(expected_type) for expected_type in self.expectedTypes])
        return 'Unexpected type(%s) of %s is given, but type(%s) is expected.' \
            % (self.getTypeStr(self.fieldValue), self.fieldName, expected_types)

    def getTypeStr(self, var_type) :
        return re.findall('\'([^\']+)\'', str(type(var_type)))[0]

class UserException(Exception) :

    def __init__(self, message = '', code = 0) :
        self.message = message
        self.code    = code

    def __str__(self) :
        return 'UserException (%s) : %s.' % (str(self.code), self.message)


# ==================== Web ====================

def request(url, getData = None, postData = None, timeout = None, method = 'GET') :
    if method == 'GET' and postData is not None :
        method = 'POST'
    try :
        if getData is not None :
            url += '?' + '&'.join(['%s=%s' % (str(key), str(value)) for key, value in getData.items()])
        data = None
        if postData is not None :
            # data = re.sub('\n', '', j(postData, indent = 0))
            data = j(safe(postData), indent = 0)
        request = urllib2.Request(url, data = data)
        response = urllib2.urlopen(request, timeout = timeout)
        content = response.read()
    except urllib2.HTTPError, e:
        # TODO
        return {'e' : 'HTTPError', 'content' : e.read()}
    except urllib2.URLError, e :
        if isinstance(e.reason, socket.timeout) :
            return {'e' : 'TIMEOUT', 'content' : None}
        else :
            print '[Other Exception]', e
            return {'e' : 'OTHER', 'content' : None}
    except socket.timeout :
        return {'e' : 'TIMEOUT', 'content' : None}
    except KeyboardInterrupt, e :
        raise
    except Exception, e:
        print postData
        print '[Unknown Exception]', e
        return {'e' : 'UNKNOWN', 'content' : None}
    else :
        return {'e' : None, 'content' : content}

# ==================== List ====================

def extend(*lists) :
    _ = []
    for __ in lists : _.extend(__)
    return _

def unique(data) : 
    _ = sorted(data)
    __ = []
    for index, item in enumerate(_) :
        if index == 0 or type(item) != type(_[index - 1]) or item != _[index - 1] :
            __.append(item)
    return __

def contains_same_items(data, check_specific_value = False, specific_value = None) :
    if type(data) not in [list, dict] :
        raise UserTypeError('data', data, [list, dict])
    if type(data) is dict : data = data.values()
    if len(data) == 0 : return True
    if check_specific_value is True :
        return data.count(specific_value) == len(data)
    else :
        return data.count(data[0]) == len(data)

# ==================== Dict ====================

def union(*dicts) :
    _ = {}
    for __ in dicts : _.update(__)
    return _

def map_to(field_names, field_values) :
    if type(field_names) is not list :
        raise UserTypeError('field_names', field_names, list)
    if type(field_values) in [int, float, bool, str, unicode] :
        return dict(zip(field_names, [field_values] * len(field_names)))
    elif type(field_values) is list :
        if len(field_values) == len(field_names) :
            return dict(zip(field_names, field_values))
        else :
            raise Exception('Lengths of field_names and field_values do not equal.\nfield_names:\n%s\nfield_values:\n%s' \
                % (j(field_names), j(field_values)))
    else :
        raise UserTypeError('field_values', field_values, [int, float, bool, str, unicode, list])

# ==================== String ====================

def strip(data, chars = ' \n\t', encoding = 'utf-8') :
    if type(data) == str :
        return data.strip(chars)
    elif type(data) == unicode :
        return data.encode(encoding).strip(chars).decode(encoding)
    elif type(data) == list :
        return [strip(datum, chars, encoding) for datum in data]
    elif type(data) == tuple :
        return (strip(datum, chars, encoding) for datum in data)
    elif type(data) == set :
        return set([strip(datum, chars, encoding) for datum in data])
    elif type(data) == dict :
        return dict([(key, strip(data[key], chars, encoding)) for key in data.keys()])
    elif type(data) in [int, float, bool] :
        return data
    else :
        raise UserTypeError('data', data, [str, unicode, list, tuple, set, dict, int, float, bool])

def safe(data, encoding = 'utf-8') :
    try :
        if type(data) is str :
            return data
        elif type(data) is unicode :
            return data.encode(encoding)
        elif type(data) is list :
            return [safe(datum, encoding) for datum in data]
        elif type(data) is tuple :
            return tuple([safe(datum, encoding) for datum in data])
        elif type(data) is set :
            return set([safe(datum, encoding) for datum in data])
        elif type(data) is dict :
            return dict([(safe(key, encoding), safe(data[key], encoding)) for key in data.keys()])
        elif type(data) in [int, float, bool] :
            return data
        elif data is None :
            return data
        else :
            raise UserTypeError('data', data, [str, unicode, list, tuple, set, dict, int, float, bool])
    except Exception, e :
        print type(data)
        print [data]
        raise e
        exit()

def contains_empty_string(data) :
    if type(data) in [str, unicode] :
        if strip(data) == '' :
            return True
        else :
            return False
    elif type(data) in [list, tuple, set] :
        for datum in data :
            if contains_empty_string(datum) :
                return True
        return False
    elif type(data) == dict :
        for key, value in data.items() :
            if contains_empty_string(value) :
                return True
        return False
    elif type(data) in [int, float, bool] :
        return False
    else :
        raise UserTypeError('data', data, [str, unicode, list, tuple, set, dict, int, float, bool])

def str_object(data) :
    if type(data) in [str, unicode, int, float, bool] :
        return data
    elif type(data) == list :
        return [str_object(datum) for datum in data]
    elif type(data) == tuple :
        return (str_object(datum) for datum in data)
    elif type(data) == set :
        return set([str_object(datum) for datum in data])
    elif type(data) == dict :
        return dict([(str_object(key), str_object(data[key])) for key in data.keys()])
    else :
        return str(data)

def unicode_to_url_hex(st) :
    res = ''
    for ch in st :
        if ch == ' ' :
            res += '%20'
        elif ord(ch) <= 128 :
            res += ch
        else :
            res += hex(ord(ch)).upper().replace('0X', '%u')
    return res

def safe_print(stream, st, encoding = 'utf-8') :
    for ch in st :
        if ord(ch) < 128 : stream.write(ch)
        else : 
            try :
                stream.write(ch.encode(encoding))
            except Exception, e :
                stream.write(ch)
    stream.flush()

# =================== Matrix ===================

def columns(matrix, column_names, set_default = False, default = None, return_only_values = False) :
    # @todo: use find
    expected_types = [list, str, unicode, int, float, bool]
    if type(column_names) not in expected_types :
        raise UserTypeError('column_names', column_names, expected_types)
    if type(column_names) is not list :
        column_names = [column_names]
    if set_default is True :
        result = find(matrix, projection = map_to(column_names, 1), raise_empty_exception = False, set_default = set_default, default = default)
    else :
        result = find(matrix, projection = map_to(column_names, 1), raise_empty_exception = True)
    if return_only_values is True :
        if len(column_names) != 1 :
            raise Exception('Can not return only values because length of column_names is not 1.\ncolumn_names:\n%s'\
                % j(column_names))
        result = [_.values()[0] for _ in result]
    return result

def column(matrix, field_name) :
    return columns(matrix, [ field_name ], return_only_values = True)

# ==================== Date ====================

def get_date_str(timestamp = None) :
    if timestamp is None : timestamp = time()
    return str(datetime.fromtimestamp(timestamp))[:10].replace('-', '.').replace('T', '.').replace(':', '.')

def generate_datetime(datestr, pattern = '%Y-%m-%d %H:%M:%S') :
    return datetime.strptime(datestr, pattern)

# ==================== Data ====================

def j(data, indent = 4, ensure_ascii = False, sort_keys = True, encoding = 'utf-8') :
    return json.dumps(data, indent = indent, ensure_ascii = ensure_ascii, sort_keys = sort_keys, encoding = encoding)

def load_txt(fin, fields = None, primary_key = None, cast = None, is_matrix = False, sep = '\t') :
    if not is_matrix :
        if fields == None :
            fields = fin.readline().strip('\n\r').split(sep)
        mapping_fields = dict([(_, fields[_]) for _ in range(len(fields))])
    if primary_key is None or is_matrix : data = []
    else : data = {}
    for line in fin :
        line = line.strip('\n\r')
        if line == '' : continue
        record = line.split(sep)
        if cast is not None and type(cast) is list :
            record = [cast[_](record[_]) for _ in range(len(record))]
        if not is_matrix : datum = dict(zip(mapping_fields.values(), record))
        else : datum = record
        if cast is not None and type(cast) is dict and not is_matrix :
            for field in cast.keys() :
                datum[field] = cast[field](datum[field])
        if primary_key is None or is_matrix: data.append(datum)
        else : data[datum[primary_key]] = datum
    return data

def dump_txt(fout, data, fields = None, primary_key = None, is_matrix = False, sep = '\t', default = '') :
    if is_matrix :
        for datum in data :
            safe_print(fout, sep.join(datum) + '\n')
            fout.flush()
    else :
        if primary_key is not None :
            data = data.values()
        if fields is None :
            fields = union(*(data)).keys()
        if primary_key is not None :
            fields.remove(primary_key)
            fields = [primary_key] + fields
        safe_print(fout, sep.join(fields) + '\n')
        for datum in data :
            safe_print(fout, sep.join([datum.get(field, default) for field in fields]) + '\n')
            fout.flush()

def load_json(fin, object_hook = None, encoding = 'utf-8') :
    return json.loads(''.join([line.strip('\n') for line in fin.readlines()]), object_hook = object_hook, encoding = encoding)

def decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = decode_list(item)
        elif isinstance(item, dict):
            item = decode_dict(item)
        rv.append(item)
    return rv

def decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = decode_list(value)
        elif isinstance(value, dict):
            value = decode_dict(value)
        rv[key] = value
    return rv

def validate_criterion(data, criterion = None) :
    if criterion is None : return True
    if criterion == {} : return True
    raise Exception('Can not handle criterion.\ncriterion:\n%s.' % j(criterion))

def perform_projection(data, projection = None, raise_empty_exception = False, set_default = False, default = None) :
    if type(data) is not dict :
        raise UserTypeError('data', data, dict)
    if projection is None : return data
    if type(projection) is not dict :
        raise UserTypeError('projection', projection, dict)
    elif not (contains_same_items(projection, True, 1) is True \
        or contains_same_items(projection, True, 0) is True) :
        raise Exception('Projection cannot have a mix of inclusion and exclusion.\nprojection:\n%s'\
            % j(projection))
    else :
        if projection == {} : return data
        # @todo: recursively...
        is_inclusion_mode = bool(sign(sum(projection.values())))
        if is_inclusion_mode is True :
            result = {}
            for field_name in projection.keys() :
                if data.has_key(field_name) is True :
                    result[field_name] = data[field_name]
                else :
                    if raise_empty_exception is True :
                        raise Exception('Field(%s) is empty, thus can not be included.\ndata:\n%s' \
                            % (str(field_name), j(data)))
                    if set_default is True :
                        result[field_name] = default
        else :
            result = data
            for field_name in projection.keys() :
                if data.has_key(field_name) is True :
                    data.pop(field_name)
                else :
                    if raise_empty_exception is True :
                        raise Exception('Field(%s) is empty, thus can not be excluded.\ndata:\n%s'\
                            % (str(field_name), j(data)))
        return result

def perform_cast(data, cast) :
    pass

def find(data, criterion = None, projection = None, raise_empty_exception = False, set_default = False, default = None) :
    if type(data) is not list :
        raise UserTypeError('data', data, list)
    if contains_same_items(map(type, data), True, dict) is False :
        raise Exception('Data does not contain just dicts.\ndata:\n%s' % j(data))
    result = []
    for datum in data :
        if validate_criterion(datum, criterion) is True:
            result.append(perform_projection(datum, projection, raise_empty_exception = raise_empty_exception, set_default = set_default, default = default))
    return result

# ==================== File ====================

def split_filename(filename) :
    if '.' in filename :
        return re.findall('(.*/)?([^/]*)\.([^\.]+)$', filename)[0]
    else : return (filename, '')

def add_prefix(filename, prefix) :
    _ = split_filename(filename)
    return _[0] + prefix + _[1] + ('' if _[2] == '' else '.') + _[2]

def add_suffix(filename, suffix) :
    _ = split_filename(filename)
    return _[0] + _[1] + suffix + ('' if _[2] == '' else '.') + _[2]

def change_ext(filename, ext) :
    _ = split_filename(filename)
    return _[0] + _[1] + ('' if _[2] == '' else '.') + ext

# ==================== Math ====================

def calc_mean(data) :
    # data = map(long, list(data))
    # tot = long(0)
    # for datum in data :
        # tot += datum
    return 1.0 * sum(data) / len(data)

def calc_std(data) :
    mean = calc_mean(data)
    return sqrt(1.0 * sum([(datum - mean) * (datum - mean) for datum in data]) / len(data))

def sign(number) :
    if type(number) not in [int, float] :
        raise UserTypeError('number', number, [int, float])
    return 0 if number == 0 else int(abs(number) / number)

def vector_product(vec1, vec2) :
    if type(vec1) is not list :
        raise UserTypeError('vec1', vec1, list)
    if type(vec2) is not list :
        raise UserTypeError('vec2', vec2, list)
    if len(vec1) != len(vec2) :
        raise Exception('Length of two vectors do not equal.')
    return [vec1[_] * vec2[_] for _ in range(len(vec1))]

def random_choice_weighted(weight_item_mapping) :
    total = sum(weight_item_mapping.keys())
    position = random.randint(1, total)
    now = 0
    for weight, item in weight_item_mapping.items() :
        now += weight
        if now >= position :
            return item
    raise Exception('random_choice_weighted failed.')

# ==================== System ====================

def parse_argv(argv) :
    mapping  = {}
    sequence = []
    for index, arg in enumerate(argv) :
        if index == 0 :
            continue
        if arg[0] == '-' :
            key, value = re.findall(r'-([^=]+)=(.*)', arg)[0]
            mapping[key] = value
        else :
            sequence.append(arg)
    return mapping, sequence

def shell(command) :
    p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    # for index, line in enumerate(p.stdout.readlines()):
        # print index, line.strip()
    retval = p.wait()
    return (p.stdout, retval)

if __name__ == '__main__' :
    print unicode_to_url_hex('happ /to')
    # weight_item_mapping = {
    #     3 : 1,
    #     7 : 2,
    #     13 : 3,
    # }
    # data = [random_choice_weighted(weight_item_mapping) for i in range(20)]
    # for item in weight_item_mapping.values() :
    #     print item, data.count(item)
    pass
