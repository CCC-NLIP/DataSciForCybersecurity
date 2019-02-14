# Data Science for Cybersecurity
_Open source code and resources arising from the ATI-funded Data Science for Cybersecurity project carried out at the University of Cambridge_

In order to use these scripts you need to obtain the CrimeBB database of hacking-related web forum posts.
Further information is available on the [Cambridge Cybercrime Centre website](https://www.cambridgecybercrime.uk/process.html).

## Contents
* CrimeBBprocessR: library of R scripts for CrimeBB analysis and automated labelling;
* Social_Network_Analysis: python and R scripts for Social Network Analysis and analysis of interests


#### CrimeBBprocessR

The models and heuristics which constitute the prediction functions in this library are described in our [Crime Science](https://crimesciencejournal.biomedcentral.com/articles/10.1186/s40163-018-0094-4) paper. 

It is assumed that you have a data frame of HackForums posts, obtained from CrimeBB. Other forums in the database have not been tested. Please contact Andrew (apc38 at cam dot ac dot uk) about adaptation of the tools to other datasets.

Thus assume you have some HackForums posts, ideally a whole set (or sets) of posts for a given thread ID (or IDs):

```
if (!require("pacman")) install.packages("pacman")
suppressMessages(library(pacman))
pacman::p_load(dbplyr, dplyr)
con <- src_postgres(dbname='crimebb')
post <- tbl(con, 'Post')
threadID <- 1238274  # for example
post.sub <- post %>% filter(Thread==threadID) %>% select(IdPost:Content, AuthorName) %>% dplyr::collect() %>% as.data.frame()
colnames(post.sub) <- c('postID', 'authorID', 'threadID', 'timestamp', 'post', 'author')
```

Then match up the posts with some info about the thread and bulletin board:
```
pacman::p_load(CrimeBBprocessR, stringr, text2vec, tidytext, nnet, tm, LiblineaR)
thread <- tbl(con, 'Thread')
thread.df <- thread %>% filter(Site==0) %>% select(IdThread, Author:Heading) %>% dplyr::collect() %>% as.data.frame()  # HF site 0
thread.sub <- subset(thread.df, IdThread==threadID)
threadTitle <- ""
bboardID <- NA
if (nrow(thread.sub)>0) {
  threadTitle <- thread.sub$Heading[1]
  threadOP <- thread.sub$AuthorName[1]
  threadOPid <- thread.sub$Author[1]
  bboardID <- thread.sub$Forum[1]
} else {  # if thread ID missing from thread table, find earliest, longest post
  earliest <- post.sub[which(post.sub$timestamp==min(post.sub$timestamp)),]
  longest <- earliest[which.is.max(nchar(earliest$post)),]  # requires nnet
  threadOP <- longest$author[1]
  threadOPid <- longest$authorID[1]
}
bboard <- tbl(con, 'Forum')
bboard.df <- bboard %>% filter(Site==0) %>% select(IdForum, Title) %>% dplyr::collect() %>% as.data.frame()  # HF site 0
bboardTitle <- ""
if (!is.null(bboardID)) {  # handle empty bulletin board IDs
  bboard.sub <- subset(bboard.df, IdForum==bboardID)
  bboardTitle <- bboard.sub$Title[1]
}
post.sub$threadTitle <- threadTitle
post.sub$threadOP <- threadOP
post.sub$threadOPid <- threadOPid
post.sub$bboardID <- bboardID
post.sub$bboardTitle <- bboardTitle
```

Now your data frame is ready for `initial_processing()`. You should by now have the following columns: `postID, authorID, 
threadID, timestamp, post, author, threadTitle, threadOP, threadOPid, bboardID, bboardTitle`.
```
df1 <- initial_processing(post.sub)
```

Next up: sentiment analysis --
```
df2 <- sentiment_scoring(df1)
```

Predict post addressee, post type and author intent:
```
df3 <- predict_addressee(df2)
df4 <- predict_posttype(df3)
df5 <- predict_intent(df4)
```

Finally, there's a call to the function which matches reputation votes to posts. This is computationally expensive (I intend to modify it) and so is best called with
the 'execute' flag set to `FALSE`. This way it returns a bunch of empty columns
```
memb.df <- data.frame()
rep.df <- data.frame()
final.df <- repvote_matching(df5, memb.df, rep.df, execute=F)
```


_Paula Buttery, Andrew Caines, Alice Hutchings, Sergio Pastrana; March 2019_
