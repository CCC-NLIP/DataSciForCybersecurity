#' Initial Processing
#'
#' First step processing of data frames from the CrimeBB database
#' Assumes at least the following columns: author, threadOP, postID, threadID, post, threadTitle
#' Depends on stringr library for str_match_all()
#' @param df Input data frame object for processing
#' @keywords preprocessing
#' @export
#' @examples
#' initial_processing(my.df)

initial_processing <- function(df) {

  # replace newlines with double backslash
  df$post <- gsub("\\n", " \\\\ ", df$post, perl=T)

  # replace double quotes with single
  df$post <- gsub("\"", "'", df$post, perl=T)

  # remove semi-colons from post and thread title (interferes with column delimiters)
  df$post <- gsub(";", "", df$post, perl=T)
  df$threadTitle <- gsub(";", "", df$threadTitle, perl=T)

  # rm punctuation from usernames while retaining a copy
  df$authorOriginal <- df$author
  df$author <- gsub('[[:punct:]]', '', df$author, perl=T)
  df$threadOPoriginal <- df$threadOP
  df$threadOP <- gsub('[[:punct:]]', '', df$threadOP, perl=T)
  
  # add index to each thread
  df$postNumber <- 0
  Ts <- unique(df$threadID)
  for (t in Ts) {
    threadArray <- which(df$threadID==t)
    df$postNumber[threadArray] <- 1:length(threadArray)
  }

  # tag first posts
  df$firstPost <- FALSE
  df$firstPost[which(df$postNumber==1)] <- TRUE

  # token count for each post
  countTokens <- function(post) {
    length(unlist(strsplit(post, ' ')))
  }
  df$tokenCount <- unlist(lapply(df$post, countTokens))

  # check for images, links, code, iframes, citations
  grepPost <- function(post, regex) {
    grepl(paste0('\\*', toupper(regex), '\\*'), post, perl=T)
  }
  df$hasImage <- unlist(lapply(df$post, regex='IMG', grepPost))
  df$hasCode <- unlist(lapply(df$post, regex='CODE', grepPost))
  df$hasLink <- unlist(lapply(df$post, regex='LINK', grepPost))
  df$hasIframe <- unlist(lapply(df$post, regex='IFRAME', grepPost))
  df$hasCitation <- unlist(lapply(df$post, regex='CITING', grepPost))

  # if citation, figure out cited user and post ID
  df$citesPostID <- ''
  df$citesUser <- ''
  for (r in 1:nrow(df)) {
    if (df$hasCitation[r]) {
      if (grepl('pid', df$post[r], perl=T)) {
        pidlist <- gsub('pid', '', unlist(str_match_all(df$post[r], 'pid[0-9]+')))
        cites <- c()
        for (pid in pidlist) {
          if (pid %in% df$postID) {  # check HF data frame for addressee username(s)
            cites <- append(cites, df$author[which(df$postID==pid)])
          }
        }
        if (length(cites)>0) {
          citing <- paste(cites, collapse=',')
        } else {
          citing <- 'external'
        }
        pid <- paste(pidlist, collapse=',')
      } else {  # else citation not well formed: fall back on OP or unknown
        pid <- 'n/a'
        if (df$firstPost[r]) {
          citing <- 'unknown'
        } else {
          citing <- df$threadOP[r]
        }
      }
      df$citesPostID[r] <- pid
      df$citesUser[r] <- citing
    }
  }

  # return
  df
}
