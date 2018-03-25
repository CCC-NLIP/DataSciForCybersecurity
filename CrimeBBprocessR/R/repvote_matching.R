#' Reputation Vote Matching
#'
#' Match user posts with reputation votes.
#' Assumes at least the following columns: timestamp, authorID, addressee
#' And a data frame for members and reputation votes already downloaded from CrimeBB database.
#' Depends on tidytext library
#' @param df Input data frame object for processing
#' @keywords reputation votes
#' @export
#' @examples
#' repvote_matching(my.df)

repvote_matching <- function(df, memb.df, rep.df, execute=T) {

  ## populate new columns
  df$addresseeID <- ""
  df$repVoteReceived <- FALSE
  df$repVoteID <- ""
  df$repVoteScore <- ""
  df$repVoteDonor <- ""
  df$repVoteTimestamp <- ""
  df$repVoteReason <- ""
  
  ## only run rep vote matching if required
  if (execute==T) {
  ## for each post...
  for (r in 1:nrow(df)) {
    tstamp <- df$timestamp[r]
    auth <- df$authorID[r]
    addr <- df$addressee[r]  # fetch addressee ID
    if (!grepl('^forum|^thread', addr, perl=T)) {  # skip forum/thread addressee
      addrID <- subset(memb.df, Username==addr)$IdMember[1]  # in case of duplicate matches (after punctuation rm)
      if (length(addrID)>0) {  # if addressee found in member table
        df$addresseeID[r] <- addrID  # keep addressee user ID
        rvmatch <- which(as.numeric(rep.df$Timestamp - tstamp)<=1 & rep.df$Donor==addrID & rep.df$Receiver==auth)  # check for match in repvotes table
        if (length(rvmatch)>0) {  # if rep vote(s) found
          df$repVoteReceived[r] <- TRUE
          rvid <- paste(rep.df$ID[rvmatch], collapse='|')  # allow for multiple votes
          df$repVoteID[r] <- rvid
          if (nrow(subset(df, repVoteID==rvid))==1) {  # only add details if first time seeing this ID
            df$repVoteScore[r] <- paste(rep.df$Quantity[rvmatch], collapse='|')
            df$repVoteDonor[r] <- paste(rep.df$Donor[rvmatch], collapse='|')
            df$repVoteTimestamp[r] <- paste(rep.df$Timestamp[rvmatch], collapse='|')
            df$repVoteReason[r] <- gsub(';', '', paste(rep.df$Reason[rvmatch], collapse='|'))  # rm semi-colons (interferes with column delimiters)
          }
        }
      }
    }
  }
  }
  
  # return
  df
}
