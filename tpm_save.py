#!/usr/bin/env python

'''

  Low Bridging Phase 1 Logger.

  It produces for each antenna and for both pols:
    -  Time domain binary data (first double word (64b) is the lenght of the following double word (64b) elements)
    -  Spectra binary data (first double word (64b) is the lenght of the following double word (64b) elements)
    -  Picture of the spectra

  Logging period depends on the load of the workstation

  When hit Ctrl+C (Keyboard Interrupt Signal) it produces
    -  A Movie (MPEG4 avi) for each antenna saved in the videos folder with subfolders for each pol

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import multiprocessing
import subprocess
import os


PYSKA_DIR = "/home/mattana/work/SKA-AAVS1/tools/pyska/"
TPMs_number = 3

def dump(job_q, results_q):
    DEVNULL = open(os.devnull, 'w')
    while True:
        FPGA_IP = job_q.get()
        if FPGA_IP == None:
            break
        try:
            print "Starting process:",'python', 'tpm_get_stream.py', '-b', FPGA_IP, '--debug'
            if subprocess.call(['python', 'tpm_get_stream.py', '-b', FPGA_IP, '--debug'], stdout=DEVNULL) == 0:
            #if subprocess.call(['python', 'tpm_get_stream.py', '--board=', FPGA_IP, '--debug'], stdout=DEVNULL) == 0:
                results_q.put(FPGA_IP)
        except:
            pass


def sort_ip_list(ip_list):
    """Sort an IP address list."""
    from IPy import IP
    ipl = [(IP(ip).int(), ip) for ip in ip_list]
    ipl.sort()
    return [ip[1] for ip in ipl]


def save_TPMs():
    pool_size = TPMs_number
    print "Starting using", TPMs_number, "TPMs"

    jobs = multiprocessing.Queue()
    results = multiprocessing.Queue()

    pool = [multiprocessing.Process(target=dump, args=(jobs, results))
            for i in range(pool_size)]

    for p in pool:
        p.start()

    for i in range(1, pool_size + 1):
        jobs.put('10.0.10.{0}'.format(i))
        # time.sleep(1)

    for p in pool:
        jobs.put(None)

    for p in pool:
        p.join()

    print
    lista_ip = []
    while not results.empty():
        lista_ip += [results.get()]
    if lista_ip == []:
        print "No iTPM boards found!"
    else:
        lista_ip = sort_ip_list(lista_ip)
        for ip in lista_ip:
            print ip
        #print lista_ip
    return lista_ip


if __name__ == "__main__":
    a = save_TPMs()
