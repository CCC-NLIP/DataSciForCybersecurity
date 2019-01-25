#' Data Preparation
#'
#' Convert CrimeBB data frame to df for model training
#' Assumes the following columns: post
#' Assumes the following columns at positions 10, 14, 15, 17:21
#' bboardID, postNumber, firstPost, hasImage, hasCode, hasLink, hasIframe, hasCitation
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
    extra.feats <- df[,c(10,14:15,17:21)]
    dtm.mx <- cbind(dtm.mx, extra.feats)
  }
  dtm.df <- as.data.frame(dtm.mx)
  # return
  dtm.df
}
