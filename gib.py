#!/usr/bin/python

# gib.py
# A backup script that uses git
# Mark Tully
# 2/9/12

#===============================================================================
# Copyright (C) 2012 by Mark Tully
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#===============================================================================

from pbs import git
import sys,os,datetime

def clearIndex():
    index=git('ls-files')
    if index.strip()!='':
        git('rm','--cached','-r','.')

def makeTreeFromDir(backupname,paths):
    """ imports a path into the git repro and makes a tree from it. returns the tree sha """
    clearIndex()
    topLevel=[]
    filesInTree=[]
    dirsInTree=[]
    for path in paths:
        if not os.path.exists(path):
            print "Path '%s' does not exist, cannot backup"%path
            sys.exit(1)
        bn=os.path.basename(path)
        if bn in topLevel:
            print "Multiple paths ending in '%s' are being backed up, not supported"%bn
            sys.exit(1)
        if os.path.isdir(path):
            # add current dir to the index (also import all objects)
            git('--work-tree',path,'add','.')
            # write the tree for this and get the tree sha
            tree=git('write-tree').strip()
            clearIndex()
            dirsInTree.append((bn,tree))
        else:
            fileHash=git('hash-object','-w',path).strip()
            filesInTree.append((bn,fileHash))
    clearIndex()
    # now make the final snapshot index
    for (dir,tree) in dirsInTree:
        git('read-tree',tree,'--prefix=%s/'%dir)
    for (file,hash) in filesInTree:
        # see http://git-scm.com/book/en/Git-Internals-Git-Objects
        # adding with 10644 means normal file (TODO perhaps check if it should be marked as executable)
        # cacheinfo means we have the hash, but no file in our work dir corresponding to it
        git('update-index','--add','--cacheinfo','10644',hash,file)
    tree=git('write-tree').strip()
    clearIndex()
    return tree

def getLatestSnapshot(backupname):
    """ returns the (sha,refname) pair for the last snapshot. returns None if there is no last snapshot """
    allRefs=str(git('show-ref'))
    snapshots=[]
    for line in str(allRefs).splitlines():
        (sha,ref)=line.split(' ',1)
        if ref.startswith('refs/gib/%s/snapshots/'%backupname):
            snapshots.append((sha,ref))
    snapshots.sort(key=lambda tup : tup[1],reverse=True)
    return snapshots[0] if len(snapshots)>0 else None

def snapshot():
    if len(sys.argv)<4:
        print 'Wrong number of parameters for snapshot command'
        sys.exit(1)
    backupname=sys.argv[2]
    backuppaths=sys.argv[3:]
    last=getLatestSnapshot(backupname)
    tree=makeTreeFromDir(backupname,backuppaths)
    if not last or tree!=last[0]:
        ref='refs/gib/%s/snapshots/%s'%(backupname,datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        git('update-ref',ref,tree)
        print 'Made snapshot %s = %s'%(ref,tree)
    else:
        print "Didn't make snapshot, no changes since last snapshot on %s"%(last[1])

def list_():
    if len(sys.argv)!=2 and len(sys.argv)!=3:
        print 'Wrong number of arguments for list command'
        sys.exit(1)
    if len(sys.argv)==2:
        # list all snapshots
        startwith='refs/gib/'
    else:
        startwith='refs/gib/%s/'%sys.argv[2]
    allRefs=str(git('show-ref'))
    for line in str(allRefs).splitlines():
        ref=line.split(' ',1)[1]
        if ref.startswith(startwith):
            print ref[9:]

def getAllRefs():
    """ returns a dict with all refs in it, keyed by reference name """
    allRefs={}
    for x in str(git('show-ref')).splitlines():
        (sha,ref)=x.split(' ',1) 
        allRefs[ref]=sha
    return allRefs

def extract():
    if len(sys.argv)!=5:
        print 'Wrong number of arguments for extract command'
        sys.exit(1)
    (backupname,snapshotname,destdir)=sys.argv[2:5]
    ref='refs/gib/%s/snapshots/%s'%(backupname,snapshotname)
    allRefs=getAllRefs()
    if ref in allRefs:
        tree=allRefs[ref]
        if os.path.exists(destdir):
            print "Destination %s' already exists - cannot extract!"%(destdir)
            sys.exit(1)
        clearIndex()
        git('read-tree',tree)
        if not destdir.endswith(os.sep):
            destdir+=os.sep
        git('checkout-index','--prefix=%s'%destdir,'-a')
        clearIndex()
        print "Extracted backup of '%s' snapshot '%s' to '%s'"%(backupname,snapshotname,destdir)
    else:
        print 'Snapshot %s for backup %s does not exist'%(snapshotname,backupname)
        print 'Tested %s'%ref
        sys.exit(1)

def usage():
    print 'gib 0.1'
    print '   A backup tool that uses git. Run from inside a git repro to backup'
    print '   files into the repro'
    print
    print 'Usage:'
    print
    print 'gib snapshot <backupname> <path to backup>+'
    print '  will take a snapshot of the given path(s) and save it'
    print '  directories will be recursively backed up and placed in a dir at the'
    print '  root level of the snapshot'
    print '  if a path is a file, the file will be backed up to the root level of'
    print '  the snapshot'
    print '  it will write the tree to refs/gib/backupname/snapshots/YYYYMMDD_HHMMSS'
    print
    print 'gib list [backupname]'
    print '  will list all available snapshots for [backupname]'
    print '  if backupname is ommitted, it will list all available snapshots for all'
    print '  backups'
    print
    print 'gib extract <backupname> <snapshotname> <destdir>'
    print '  extract a backup to the directory <destdir>'
    print '  <destdir> must not already exist'
    print

if __name__ == "__main__":
    if not os.path.isdir('.git'):
        fatal("Should be ran from inside the git repro")
        sys.exit(1)
    if len(sys.argv)==1:
        usage()
        sys.exit(1)
    if sys.argv[1]=='snapshot':
        snapshot()
    elif sys.argv[1]=='list':
        list_()
    elif sys.argv[1]=='extract':
        extract()
    elif sys.argv[1]=='help' or sys.argv[1]=='--help':
        usage()
    else:
        print 'Unknown command %s'%sys.argv[1]
        sys.exit(1)
