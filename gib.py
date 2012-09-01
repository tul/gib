from pbs import git
import sys,os,datetime

def makeTreeFromDir(backupname,path):
    """ imports a path into the git repro and makes a tree from it. returns the tree sha """
    def clearIndex():
        index=git('ls-files')
        if index.strip()!='':
            git('--work-tree',path,'rm','--cached','-r','.')
    clearIndex()
    # add current dir to the index (also import all objects)
    git('--work-tree',path,'add','.')
    # write the tree for this and get the tree sha
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
    if len(sys.argv)!=4:
        print 'Wrong number of parameters for snapshot command'
        sys.exit(1)
    backupname=sys.argv[2]
    backuppath=sys.argv[3]
    last=getLatestSnapshot(backupname)
    tree=makeTreeFromDir(backupname,backuppath)
    if not last or tree!=last[0]:
        ref='refs/gib/%s/snapshots/%s'%(backupname,datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        git('update-ref',ref,tree)
        print 'Made snapshot %s = %s'%(ref,tree)
    else:
        print "Didn't make snapshot, no changes since last snapshot on %s"%(last[1])

def usage():
    print 'usage:'
    print 'gib snapshot <backupname> <path to backup>'
    print 'will take a snapshot of the given path and save it'
    print 'it will write the tree to refs/gib/backupname/snapshots/YYYYMMDD_HHMMSS'

if __name__ == "__main__":
    if not os.path.isdir('.git'):
        fatal("Should be ran from inside the git repro")
        sys.exit(1)
    if len(sys.argv)==1:
        usage()
        sys.exit(1)
    if sys.argv[1]=='snapshot':
        snapshot()
