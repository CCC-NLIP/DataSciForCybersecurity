#' Data Preparation
#'
#' Convert CrimeBB data frame to df for model training
#' Assumes the following columns: post
#' Assumes the following columns at positions 9,10,11,12,13,17,24,26,27,31,32:
#' hasImage, hasLink, hasCode, hasIframe, hasCitation, addressOP, forumID, firstPost, threadCount, authorIsOP, citesOP
#' Dependencies: tm, xgboost
#' @param df Input data frame object for processing
#' @keywords preprocessing, machine learning
#' @export
#' @examples
#' data_prep(my.df)

data_prep <- function(df, xgb=F) {
  corpus <- VCorpus(VectorSource(df$post))
  dtm.mx <- as.matrix(DocumentTermMatrix(corpus, control=list(removePunctuation=T, stopwords=T, stemming=F, removeNumbers=T, minDocFreq=2, weighting=TfIdf)))
  if (!xgb) {
    extra.feats <- df[,c(9:13,17,24,26,27,31,32)]
    dtm.mx <- cbind(dtm.mx, extra.feats)
  }
  dtm.df <- as.data.frame(dtm.mx)
  # return
  dtm.df
}
