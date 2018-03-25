#' User Stats
#'
#' Summary user stats based on posts extracted from CrimeBB database.
#' Assumes a posts data frame with at least the following columns: repVoteReceived, timestamp, threadID, firstPost, bboardID, tokenCount, sentiment, hasImage, hasCode, hasLink, hasIframe, hasCitation (all pre-processed)
#' And a subset of the member table from CrimeBB.
#' And reputation vote data frame downloaded from CrimeBB database.
#' @param df Input data frame object for processing
#' @keywords user analysis
#' @export
#' @examples
#' user_stats(my.df)

user_stats <- function(df.in, thread.df, memb.df, rep.df) {

  userID <- memb.df$IdMember[1]
  user <- memb.df$Username[1]
  age <- memb.df$Age[1]
  hoursSpent <- memb.df$TimeSpent[1]
  nPosts <- nrow(df.in)
  startPost <- min(df.in$timestamp)
  lastPost <- max(df.in$timestamp)
  nDaysActive <- round(as.numeric(lastPost-startPost), 0)
  nThreadsInvolved <- length(unique(df.in$threadID))
  nThreadsStarted <- sum(df.in$firstPost)
  nBboardsInvolved <- length(unique(df.in$bboardID))
  nWordTokens <- sum(df.in$tokenCount)
  meanSentiment <- mean(df.in$sentiment)
  imageRate <- round(sum(df.in$hasImage/nPosts), 3)
  codeRate <- round(sum(df.in$hasCode/nPosts), 3)
  linkRate <- round(sum(df.in$hasLink/nPosts), 3)
  iframeRate <- round(sum(df.in$hasIframe/nPosts), 3)
  citationRate <- round(sum(df.in$hasCitation/nPosts), 3)
  reputation <- memb.df$Reputation[1]
  prestige <- memb.df$Prestige[1]
  nRepVotesReceived <- nrow(subset(rep.df, Receiver==userID))
  nRepVotesGiven <- nrow(subset(rep.df, Donor==userID))
  commonBoardProp <- round(nrow(subset(subset(thread.df, topic=='common'), df.in$threadID %in% threads)) / nPosts, 4)
  hackBoardProp <- round(nrow(subset(subset(thread.df, topic=='hacking'), df.in$threadID %in% threads)) / nPosts, 4)
  techBoardProp <- round(nrow(subset(subset(thread.df, topic=='tech'), df.in$threadID %in% threads)) / nPosts, 4)
  codingBoardProp <- round(nrow(subset(subset(thread.df, topic=='coding'), df.in$threadID %in% threads)) / nPosts, 4)
  gamingBoardProp <- round(nrow(subset(subset(thread.df, topic=='gaming'), df.in$threadID %in% threads)) / nPosts, 4)
  marketBoardProp <- round(nrow(subset(subset(thread.df, topic=='market'), df.in$threadID %in% threads)) / nPosts, 4)
  moneyBoardProp <- round(nrow(subset(subset(thread.df, topic=='money'), df.in$threadID %in% threads)) / nPosts, 4)
  webBoardProp <- round(nrow(subset(subset(thread.df, topic=='web'), df.in$threadID %in% threads)) / nPosts, 4)
  graphicsBoardProp <- round(nrow(subset(subset(thread.df, topic=='graphics'), df.in$threadID %in% threads)) / nPosts, 4)

  df.out <- data.frame(userID, user, age, hoursSpent, nPosts, startPost, lastPost, nDaysActive, nThreadsInvolved, nThreadsStarted, nBboardsInvolved, nWordTokens, meanSentiment, imageRate, codeRate, linkRate, iframeRate, citationRate, reputation, prestige, nRepVotesReceived, nRepVotesGiven, commonBoardProp, hackBoardProp, techBoardProp, codingBoardProp, gamingBoardProp, marketBoardProp, moneyBoardProp, webBoardProp, graphicsBoardProp)

  # return
  df.out
}
