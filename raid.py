
import sys
import os
from struct import pack, unpack
from math import sqrt
from random import randint
import numpy as np
import numpy.linalg as lin
import shutil

class Agent:
    pass

class Token:
    pass
    
class Metadata:
    pass    

global agent_list
global token
global agent_count
global synd_count
global photo_count
global local_voting_param
global compare_param
global timeout_param

timeout_param = 100
compare_param = 0.4
local_voting_param = 0.1

file_type_param = 'png'
file_size_min_param = 50
file_size_max_param = 150

mode = int(sys.argv[1])
agent_count = int(sys.argv[2])
stripe_count = int(sys.argv[3])
synd_count = int(sys.argv[4])

agent_list = []
token = Token()

for agent_num in range(agent_count):
    agent = Agent()
    agent.number = agent_num
    agent_list.append(agent)
    
def delete_files():
    for agent_num in range(agent_count):
        if os.path.exists(str(agent_num)):
            shutil.rmtree(str(agent_num), ignore_errors=True)

def create_files():
    delete_files()
    for agent_num in range(agent_count):
        if not os.path.exists(str(agent_num)):
            os.makedirs(str(agent_num))

    for stripe_num in range(stripe_count):
        synd_agent_list = []
        for synd_num in range(synd_count):
            synd_agent_list.append((stripe_num + synd_num) % agent_count)
        
        for agent_num in range(agent_count):
            if agent_num in synd_agent_list:
                continue

            fsize = randint(file_size_min_param, file_size_max_param)
            fdata = ''
            for byte_num in range(fsize):
                fdata += pack('B', randint(0, 255))

            fname = '{}/{}.{}'.format(agent_num, stripe_num, file_type_param)
            file = open(fname, 'wb')
            file.write(fdata)
            file.close()

def init_agents():
    for agent in agent_list:
        agent.average = []
        agent.tmp_average = []

def init_meta(meta):
    meta.agent_size = 0
    meta.fsize_list = []

def is_neighbor_ring_topology(agent, agent_neighbor, count):
    if count % 2 == 0:
        if ((agent.number % 2 == 0 and
             (abs(agent.number - agent_neighbor.number) == 1 or
              abs(agent.number - agent_neighbor.number) == agent_count - 1) and
             agent.number < agent_neighbor.number) or
            (agent.number % 2 == 1 and
             (abs(agent.number - agent_neighbor.number) == 1 or
              abs(agent.number - agent_neighbor.number) == agent_count - 1) and
             agent.number > agent_neighbor.number)):
            return True
    elif count % 2 == 1:
        if ((agent.number % 2 == 0 and
             abs(agent.number - agent_neighbor.number) == 1 and
             agent.number > agent_neighbor.number) or
            (agent.number % 2 == 1 and
             abs(agent.number - agent_neighbor.number) == 1 and
             agent.number < agent_neighbor.number)):
            return True
    return False

def is_neighbor_cell_topology(agent, agent_neighbor, count):
    if (abs(agent.number - agent_neighbor.number) == 1 or
        abs(agent.number - agent_neighbor.number) == int(sqrt(agent_count)) or
        abs(agent.number - agent_neighbor.number) == int(sqrt(agent_count)) - 1 or
        abs(agent.number - agent_neighbor.number) == int(sqrt(agent_count)) + 1):
        return True
    return False
    
def is_neighbor_all_topology(agent, agent_neighbor, count):
    if agent.number != agent_neighbor.number:
        return True
    return False

def init_token(token, stripe_num):
    token.agent_num = 0
    token.count = 0
    token.state = 'check'
    token.average = []
    token.meta = Metadata()
    init_meta(token.meta)
    token.synd_agent_list = [(stripe_num + synd_num) % agent_count for synd_num in range(synd_count)]

def read_data_file(agent, agent_size, stripe_num):
    fname = '{}/{}.{}'.format(agent.number, 
                              stripe_num, 
                              file_type_param)
    if not os.path.exists(fname):
        print 'File {} is not found!'.format(fname)
        return
    file = open(fname, 'rb')
    fdata = file.read()
    file.close()

    agent.tmp_average = [0.0] * agent_size
    count = len(fdata)
    agent.average = []
    for data_num in range(agent_size):
        if (data_num + 1) * 4 <= count:
            data = fdata[data_num * 4:(data_num + 1) * 4]
            number = unpack('I', data)[0]
        elif data_num * 4 <= count:
            data = fdata[data_num * 4:]
            data = data.ljust(4, '\x00')
            number = unpack('I', data)[0]
        else:
            number = 0
        agent.average.append(float(number)) 

def check_data_file(agent, meta, stripe_num):
    fname = '{}/{}.{}'.format(agent.number, 
                              stripe_num, 
                              file_type_param)
    if os.path.exists(fname):
        fsize = os.path.getsize(fname)
        meta.fsize_list.append(fsize)
        if fsize > meta.agent_size:
            meta.agent_size = fsize
    else:
        print 'File {} is not found!'.format(fname)

def local_voting_calculate(token, agent):
    for data_num in range(token.meta.agent_size):
        agent.tmp_average[data_num] = 0.0
        for agent_neighbor in agent_list:
            if is_neighbor_all_topology(agent, agent_neighbor, token.count) == True:
                agent.tmp_average[data_num] += agent.average[data_num] - agent_neighbor.average[data_num]
        agent.tmp_average[data_num] = agent.average[data_num] - local_voting_param * agent.tmp_average[data_num]

def write_meta_file(agent, meta, stripe_num):
    fdata = pack('I', meta.agent_size)
    for fsize in meta.fsize_list:
        fdata += pack('I', fsize)

    fname = '{}/{}.meta'.format(agent.number, stripe_num)
    file = open(fname, 'wb')
    file.write(fdata)
    file.close()
    
def read_meta_file(agent, meta, stripe_num):
    fname = '{}/{}.meta'.format(agent.number, stripe_num)
    if not os.path.exists(fname):
        print 'File {} is not found!'.format(fname)
        return
    file = open(fname, 'rb')
    fdata = file.read()
    file.close()

    data = fdata[0:4]
    meta.agent_size = unpack('I', data)[0]
    
    count = len(fdata) / 4 - 1
    meta.fsize_list = []
    for data_num in range(count):
        data = fdata[(data_num + 1) * 4:(data_num + 2) * 4]
        fsize = unpack('I', data)[0]
        meta.fsize_list.append(fsize)
        
def write_data_file(agent, meta, stripe_num):
    buffer_num = agent_to_buffer_num(agent, stripe_num)
    fsize = meta.fsize_list[buffer_num]
    fdata = ''
    for data in agent.average:
        fdata += pack('I', int(data))
    fdata = fdata[:fsize]

    fname = '{}/{}.{}'.format(agent.number, 
                              stripe_num, 
                              file_type_param)
    file = open(fname, 'wb')
    file.write(fdata)
    file.close()
        
def write_syndrom(agent, stripe_num):
    fdata = ''
    for data in agent.average:
        fdata += pack('Q', int(round(data * agent_count)))

    fname = '{}/{}.synd'.format(agent.number, stripe_num)
    file = open(fname, 'wb')
    file.write(fdata)
    file.close()

def read_syndrom(agent, agent_size, stripe_num):
    fname = '{}/{}.synd'.format(agent.number, stripe_num)
    if not os.path.exists(fname):
        print 'File {} is not found!'.format(fname)
        return
    file = open(fname, 'rb')
    fdata = file.read()
    file.close()

    count = len(fdata)
    agent.average = []
    for data_num in range(agent_size):
        if (data_num + 1) * 8 <= count:
            data = fdata[data_num * 8:(data_num + 1) * 8]
            number = unpack('Q', data)[0]
        elif data_num * 8 <= count:
            data = fdata[data_num * 8:]
            data = data.ljust(8, '\x00')
            number = unpack('Q', data)[0]
        else:
            number = 0
        agent.average.append(float(number))        

def agent_to_buffer_num(agent, stripe_num):
    data_agent_count = agent_count - synd_count;
    first_synd_agent_num = stripe_num % agent_count;

    if first_synd_agent_num + synd_count <= agent_count:
        if agent.number < first_synd_agent_num:
            ret = agent.number;
        elif agent.number >= first_synd_agent_num + synd_count:
            ret = agent.number - synd_count;
        else:
            ret = agent.number + data_agent_count - first_synd_agent_num;
    else:
        if agent.number >= first_synd_agent_num:
            ret = agent.number + data_agent_count - first_synd_agent_num
        elif agent.number < first_synd_agent_num + synd_count - agent_count:
            ret = agent.number + agent_count - first_synd_agent_num + data_agent_count
        else:
            ret = agent.number - (first_synd_agent_num + synd_count - agent_count)
    return ret

def restore_stripe(stripe_num, absent_agent_set):
    meta = Metadata()
    init_meta(meta)
    init_agents()

    synd_agent_set = {(stripe_num + synd_num) % agent_count for synd_num in range(synd_count)}
    data_agent_set = {agent_num for agent_num in range(agent_count)} - synd_agent_set
    absent_data_agent_set = absent_agent_set - synd_agent_set
    present_data_agent_set = data_agent_set - absent_agent_set
    present_synd_agent_set = synd_agent_set - absent_agent_set
    
    absent_data_agent_count = len(absent_data_agent_set)
    present_synd_agent_count = len(present_synd_agent_set)
    
    if absent_data_agent_count == 0:
        return
    
    count = present_synd_agent_count - absent_data_agent_count
    for present_synd_agent_num in range(count):
        present_synd_agent_set.pop()
        
    agent_num = present_synd_agent_set.pop()
    agent = agent_list[agent_num]
    read_meta_file(agent, meta, stripe_num)
    present_synd_agent_set.add(agent_num)
    
    present_synd_dict = {}
    for present_synd_agent_num in present_synd_agent_set:
        agent = agent_list[present_synd_agent_num]
        present_synd_num = agent_to_buffer_num(agent, stripe_num) - (agent_count - synd_count)
        present_synd_dict.update({present_synd_agent_num : present_synd_num})

    for agent in agent_list:
        if agent.number in present_data_agent_set:
            read_data_file(agent, meta.agent_size, stripe_num)
        elif agent.number in present_synd_agent_set:
            read_syndrom(agent, meta.agent_size, stripe_num)
        else:
            agent.average = [0.0] * meta.agent_size
    
    for present_synd_agent_num in present_synd_agent_set:
        present_synd_num = present_synd_dict[present_synd_agent_num]
        agent_with_synd = agent_list[present_synd_agent_num]
        for agent_num in present_data_agent_set:
            agent = agent_list[agent_num]
            buffer_num = agent_to_buffer_num(agent, stripe_num)
            agent.tmp_average = map(lambda x: ((present_synd_num + 1) ** buffer_num) * x, agent.average)
            for data_num in range(meta.agent_size):
                agent_with_synd.average[data_num] -= agent.tmp_average[data_num]

    for data_num in range(meta.agent_size):
        a_list = []
        b_list = []
        for present_synd_agent_num in present_synd_agent_set:
            present_synd_num = present_synd_dict[present_synd_agent_num]
            agent_with_synd = agent_list[present_synd_agent_num]
            vandermonde_list = []
            for absent_data_agent_num in absent_data_agent_set:
                agent = agent_list[absent_data_agent_num]
                buffer_num = agent_to_buffer_num(agent, stripe_num)
                vandermonde_list.append((present_synd_num + 1) ** buffer_num)
            a_list.append(vandermonde_list)
            b_list.append(agent_with_synd.average[data_num])
        
        a = np.array(a_list)
        b = np.array(b_list)
        x = lin.solve(a, b)
        print x
        
        decision_num = 0
        for absent_data_agent_num in absent_data_agent_set:
            agent = agent_list[absent_data_agent_num]
            agent.average[data_num] = x[decision_num]
            decision_num += 1
    
    for absent_data_agent_num in absent_data_agent_set:
        agent = agent_list[absent_data_agent_num]
        write_data_file(agent, meta, stripe_num)

def restore_files():
    absent_agent_set = set()
    for agent_num in range(agent_count):
        if not os.path.exists(str(agent_num)):
            absent_agent_set.add(agent_num)
            
    if len(absent_agent_set) == 0:
        return
        
    if len(absent_agent_set) > synd_count:
        print 'Too many absent agent!'
        return
    
    for agent_num in absent_agent_set:
        os.makedirs(str(agent_num))
    
    for stripe_num in range(stripe_count):
        restore_stripe(stripe_num, absent_agent_set)

def calculate_syndrom(stripe_num, synd_num):
    init_agents()
    init_token(token, stripe_num)

    while True:
        agent = agent_list[token.agent_num]
        meta = token.meta
        
        if token.state == 'check':
            if not agent.number in token.synd_agent_list:
                check_data_file(agent, meta, stripe_num)
            
            if token.agent_num == agent_count - 1:
                meta.agent_size = (meta.agent_size + 3) / 4
                token.state = 'init'
                token.agent_num = 0
            else:
                token.agent_num += 1
            continue
        
        if token.state == 'init':
            if agent.number in token.synd_agent_list:
                agent.average = [0.0] * meta.agent_size
                agent.tmp_average = [0.0] * meta.agent_size
            else:
                read_data_file(agent, meta.agent_size, stripe_num)
                buffer_num = agent_to_buffer_num(agent, stripe_num)
                agent.average = map(lambda x: ((synd_num + 1) ** buffer_num) * x, agent.average)
            
            if token.agent_num == agent_count - 1:
                token.state = 'calculate'
                token.agent_num = 0
            else:
                token.agent_num += 1
            continue

        if token.state == 'write syndrom':
            if agent.number == token.synd_agent_list[synd_num]:
                write_syndrom(agent, stripe_num)
            write_meta_file(agent, meta, stripe_num)
            
            if token.agent_num == agent_count - 1:
                break
            else:
                token.agent_num += 1
            continue

        if token.state == 'calculate':
            local_voting_calculate(token, agent)

            if token.agent_num == agent_count - 1:
                token.state = 'end all'
                token.agent_num = 0
            else:
                token.agent_num += 1
            continue

        for number in range(meta.agent_size):
            agent.average[number] = agent.tmp_average[number]
        
        if token.agent_num == 0:
            if len(token.average) == 0:
                token.average = [0.0] * meta.agent_size
            for number in range(meta.agent_size):
                token.average[number] = agent.average[number]
        elif token.count < timeout_param:
            for number in range(meta.agent_size):
                if abs(token.average[number] - agent.average[number]) * (agent_count**2) > compare_param:
                    token.state = 'end tick'
                token.average[number] = agent.average[number]
        
        if token.agent_num == agent_count - 1:
            token.count += 1
            if token.state == 'end all':
                token.state = 'write syndrom'
                token.agent_num = 0
            else:
                token.state = 'calculate'
                token.agent_num = 0
        else:
            token.agent_num += 1

if mode == 0:
    create_files()
elif mode == 1:
    for stripe_num in range(stripe_count):
        for synd_num in range(synd_count):
            calculate_syndrom(stripe_num, synd_num)
elif mode == 2:
    restore_files()
elif mode == 3:
    delete_files()
