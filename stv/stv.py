import csv
import argparse
import sys

parser = argparse.ArgumentParser(description='Calculate the winner of an election using IRV or STV.', epilog='To have it print detailed results, use -v. Since we tend to use droop for most results, that is the default, but you can change it to hare by using `-q hare`')
parser.add_argument('nseats', type=int,  help='The number of seats available during the election (use 1 for an IRV election)')
parser.add_argument('file', type=str,  help='The path to the csv file containing the vote data')
parser.add_argument('-q', '--quota', type=str, default = 'droop', choices=['hare','droop'], help='The quota to use for the election, use `-q hare` for hare, and `-q droop` for droop')
parser.add_argument('-i', '--interactive', action='store_true', help='Whether the program should ask for confirmation before calculating each round (do not use this without -v)')
parser.add_argument('-v', '--verbose', action='store_true', help='Toggle complete output for each round, instead of just printing the winners.')
args = parser.parse_args()
def vprint(message):
    if args.verbose:
        print(message)
def count(v,w,n):
    c = [0]*len(n)
    for j in range(len(v)):
        e = v[j]
        if '1' in e:
            i = e.index('1')
            c[i] += w[j]
    return c
def winupdate(i,v,w,c,q):
    factor = 1-q/c[i]
    vprint("Winning ballots go to next round reweighted by a factor of "+str(factor))
    for c in range(len(v)):
        e = v[c]
        if e[i] == '1':
            for j in range(len(e)):
                e[j] = str(int(e[j])-1)
            if '1' in e:
                while e.index('1') in elimset:
                    for j in range(len(e)):
                        e[j] = str(int(e[j]) - 1)
                    if '1' not in e:
                        break
            w[c] = factor*float(w[c])
    elimset.add(i)
    return
def lossupdate(i,v):
    for c in range(len(v)):
        e = v[c]
        if e[i] == '1':
            for j in range(len(e)):
                e[j] = str(int(e[j])-1)
            if '1' in e:
                while e.index('1') in elimset:
                    for j in range(len(e)):
                        e[j] = str(int(e[j]) - 1)
                    if '1' not in e:
                        break
    elimset.add(i)
    return
seats = args.nseats
seatsleft = args.nseats
votes = []
voteweights = []
qtype = None
with open(args.file) as file:  # put the path to the csv file here
    lines = csv.reader(file)
    f = 0
    for l in lines:
        if f == 0:
            namelist = l
            f = 1
            names = []
            for candname in namelist:
                if candname:
                    names.append(candname)
                else:
                    break
            wid = len(names)

        else:
            gl = []
            for i in range(wid):
                e = l[i]
                if e == 'Abstain':
                    gl.append('0')
                else:
                    gl.append(e)
            votes.append(gl)
            voteweights.append(1)

qtype = args.quota
if qtype=="hare":
        quota = len(votes) / seats
        vprint("The Hare quota is equal " + str(quota))
elif qtype=="droop":
        quota = int(len(votes)/(seats+1))+1
        vprint("The Droop quota is equal "+str(quota))
else:
        print('Unknown quota, exiting...')
        sys.exit(1)

candidatesleft = len(names)

nameline = ' '.join(['{:^7.7}'.format(nam) for nam in names])

winners = []
elimset = set()
n = 1
while seatsleft > 0:
    if n > 1 and args.interactive:
        dummy = input("Press enter to calculate next round")
    vprint("Round "+str(n))
    foundwinner = 0
    actcount = count(votes,voteweights,names)
    vprint(nameline)
    vprint(' '.join(['{:^7.3f}'.format(i) for i in actcount]))
    w = 0
    leastvotes = len(votes)
    for cand in actcount:
        if cand >= quota:
            vprint(names[w]+" won a seat!")
            winners.append(names[w])
            winupdate(w,votes,voteweights,actcount,quota)
            seatsleft -= 1
            candidatesleft -= 1
            foundwinner = 1
        else:
            if cand < leastvotes and cand > 0:
                leastvotes = float(cand)
                loser = int(w)
        w += 1
    if foundwinner == 0:
        vprint(names[loser]+" lost!")
        lossupdate(loser,votes)
        candidatesleft -= 1
    if seatsleft == candidatesleft:
        winset = set(range(len(names)))-elimset
        vprint(" and ".join([names[i] for i in list(winset)])+" win the remaining seats!")
        for i in list(winset):
            winners.append(names[i])
        break
    n += 1
print('The winner(s) are: ' + " and ".join(winners))