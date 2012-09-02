gib - A backup tool that uses git
=================================

Mark Tully
2/9/12

Overview
--------
This tool will backup directories and files into a git repro. It doesn't require the files to be in a git working tree, it just copies them from wherever they are into the backup repro as it backs them up.

Good things
-----------
* Can push and pull backups between machines using normal git commands
* Integrity checking is provided by git sha mechanism
* Delta compression for free
* Can purge old backups by deleting refs and then garbage collecting the repro

Bad things
----------
* Git doesn't record file level permissions, including owner and group, so these are not backed up

Usage
-----
First you need a git repro to backup into. You can use one repro for several different backup sources, or give each one its own repro, it's up to you. If you are backing up several distinct sources into the same repro, they will not interfere with each other. However, if they have any files in common, then the overall space for the backup will be reduced due to they way git stores unique files.

Let's create a new repro:

> > mkdir backups
> > cd backups
> > git init

Now backup some file (note these commands are executed from within the git repro, like any other git command)

> > gib.py snapshot mybackup ../../mydir 
> Made snapshot refs/gib/mybackup/snapshots/20120902_014904 = 94adf1a14c7e172836352e048b870c2fdba576ff

This snapshot command has imported the contents of 'mydir' into the repro and tagged the resulting tree with the current time and the symbolic name 'mybackup'. If you do it again and mydir has not changed it doesn't create a new ref:

> > gib.py snapshot mybackup ../../mydir 
> Didn't make snapshot, no changes since last snapshot on refs/gib/mybackup/snapshots/20120902_014904

To list the available backups:

> > gib.py list
> mybackup/snapshots/20120902_014904

To extract a backup:

> > gib.py extract mybackup 20120902_014904 somedir
> Extracted backup of 'mybackup' snapshot '20120902_014904' to 'somedir/' 

How I use it
------------
On a web server with a blog and uploads etc, I first dump the MySQL database to a tmp file, taking care to provide the --skip-dump-date option to mysqldump to ensure the file only changes if the database has changed. I then use gib to backup the dumped SQL file and the blog dir (which also includes all uploaded files) into the gib backup repro. I do this every 24 hours. If I want to sync a snapshot from home, I use git to fetch the ref of the snapshot I'm interested in and it pull just the files in that snapshot that I do not already have. I can then extract it to a directory, import the DB and run my local webserver.



This has been put on gibhub in case someone else finds it useful :)
