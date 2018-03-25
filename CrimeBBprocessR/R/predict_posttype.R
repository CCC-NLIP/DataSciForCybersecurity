#' Predict Post Type
#'
#' Predict the type of each post in a CrimeBB dataset.
#' Assumes at least the following columns: post, bboardTitle, firstPost (last column comes from initial_processing() function).
#' Dependencies: tm, LiblineaR
#' @param df Input data frame object for processing, and optional trained model, document-term matrix and list of labels used in model training.
#' @keywords post type
#' @export
#' @examples
#' predict_posttype(my.df)

predict_posttype <- function(df, model=NULL, train.dtm=NULL, labs=NULL) {

  # load linear model pre-trained by postTypeAuthorIntentAddresseeExperiments.R
  if (is.null(model)) {
    model <- readRDS('postType_LM.rds')
  }
  # plus associated training data
  if (is.null(train.dtm)) {
    train.dtm <- readRDS('postType_dtm.rds')
  }
  # and label set (needed with e.g. XGBoost, not LM)
  #if (is.null(labs)) {
  #  labs <- readRDS('postType_labels.rds')
  #}

  df$postType <- ''
  for (r in 1:nrow(df)) {
    # if first post and in listed bulletin board
    if ((df$firstPost[r]) & (grepl('[Tt]rading|[Ss]ellers|[Bb]azaar|[Mm]arket^p', df$bboardTitle[r], perl=T))) {
      df$postType[r] <- 'offerX'  # trading BBs tend to start with an offer
    } else {
      test.dtm <- data_prep(df[r,])
      xTest <- matrix_align(train.dtm, test.dtm)
      df$postType[r] <- as.character(predict(model, xTest, proba=F, decisionValues=T)$predictions)
    }
  }

  # return
  df
}
