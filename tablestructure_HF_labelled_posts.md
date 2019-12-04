# Table description: HF_labelled_posts

A description of the contents of the `HF_labelled_posts` table in the CrimeBB database, hosted by the Cambridge Cybercrime Centre (CCC).


### Background

41 million HackForums posts were automatically labelled for a number of properties (type of post, author's intent, addressee) as part of the CCC & NLIP collaboration at the University of Cambridge Computer Laboratory [1], [2], [3].

The process was last run in early 2019: all HF posts which were in CrimeBB on 12 March have been labelled.


### CrimeBB

To access CrimeBB I connect to shalmaneser6 and use the RPostgreSQL library for R:

```
if (!require("pacman")) install.packages("pacman")
suppressMessages(library(pacman))
pacman::p_load(RPostgreSQL, dbplyr, dplyr)

con <- src_postgres(dbname='crimebb')
hf <- tbl(con, 'HF_labelled_posts')
hf.df <- hf %>% dplyr::collect() %>% as_tibble()
# takes some time...
```


### HF_labelled_posts

The columns in this table are described below. Note that the post texts are not stored in this table, to save space; to get these you'll need to query the 'Post' table with the site ID for HackForums (0) and post ID from this table.

Key terminology: thread = a set of posts about a topic set by the first post (original post, OP); bulletin board (bboard) = set of threads about a topic declared by forum admins.

| Column | Description | Example |
|---|---|---|
| postID      | unique identifier of the post (note that other forums can have matching postIDs; disambiguate with siteID=0) | 5064170 |
| authorID      | unique identifier for the post author | 188708 |
| threadID      | unique identifier of the thread | 532721 |
| timestamp      | timestamp when the post was published | 2010-07-10 16:44:00 UTC |
| author      | username of the post author | CometJack |
| threadOP      | username of the OP author | Shock3r2010 |
| threadOPid      | unique identifier of the OP author | 381043 |
| bboardID      | unique identifier of the bulletin board | 118 |
| authorOriginal      | username of the post author (before punctuation removal) | psyx:soul |
| threadOPoriginal      | username of the OP author (before punctuation removal) | psyx:soul |
| postNumber      | ordinal number of the post within its thread, from 1 | 1,2,3... |
| firstPost      | logical: first post in thread? | TRUE/FALSE |
| tokenCount      | number of word tokens in this post | 22, 19, 59 |
| hasImage      | this post features an image | TRUE/FALSE |
| hasCode      | this post features a code snippet | TRUE/FALSE |
| hasLink      | this post features a link| TRUE/FALSE |
| hasIframe      | this post features an iframe | TRUE/FALSE |
| hasCitation      | this post features a citation of another post | TRUE/FALSE |
| citesPostID      | unique identifier of the cited post | 5064170 |
| citesUser      | username of the author of the cited post | CometJack |
| sentiment      | automatically assigned sentiment score based on typical sentiment of words used in the post | 0.09790210, -0.01694915 |
| addressee      | username of the addressee of the post | Shock3r2010 |
| addresseeType      | type of addressee (auto assigned) | closed set: {other,threadOP,general} |
| postType      | type of post (auto assigned) | closed set: {comment,exchange,infoRequest,tutorial,offerX,social,requestX} |
| intent      | the author's intent (auto assigned; note: can be multiple labels) | closed set: {neutral,positive,gratitude,aggression,negative,vouch,moderate,privatemessage} |
| addresseeID      | unique identifier of the addressee (auto assigned) | 188708 |
| repVoteReceived      | logical: reputation vote associated with this post? (not run) | - |
| repVoteID      | unique identifier of the reputation vote | - |
| repVoteScore      | reputation vote score | - |
| repVoteDonor      | unique identifier of the reputation vote giver | - |
| repVoteTimestamp      | timestamp of the reputation vote | - |
| repVoteReason      | comment associated with the reputation vote | - |
| postthread      | post ID and thread ID, concatenated with an underscore | 5064170_532721 |


_Andrew Caines, December 2019_

[1] Sergio Pastrana, Alice Hutchings, Andrew Caines & Paula Buttery. Characterizing Eve: Analysing Cybercrime Actors in a Large Underground Forum. [Proceedings of the 21st International Symposium on Research in Attacks, Intrusions and Defenses (RAID 2018)](https://www.cl.cam.ac.uk/~sp849/files/RAID_2018.pdf).

[2] Andrew Caines, Sergio Pastrana, Alice Hutchings & Paula Buttery. Automatically identifying the function and intent of posts in underground forums. [Crime Science 7:19](https://link.springer.com/article/10.1186/s40163-018-0094-4).

[3] Andrew Caines, Sergio Pastrana, Alice Hutchings & Paula Buttery. Aggressive language in an online hacking forum. [Proceedings of the 2nd Abusive Language Workshop (ALW 2018)](https://www.aclweb.org/anthology/W18-5109).

