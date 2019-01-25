#' Predict Addressee
#'
#' Identifies most likely addressee on basis of position in thread, isThreadOP or not, cited post (if present)
#' Assumes at least the following columns: postID, post, author, threadID, threadOP; firstPost, postNumber, hasCitation, citesPostID, citesUser (last 5 columns come from initial_processing() function).
#' @param df Input data frame object for processing
#' @keywords addressee, conversation analysis
#' @export
#' @examples
#' predict_addressee(my.df)

predict_addressee <- function(df, model=NULL, train.dtm=NULL, labs=NULL) {
  # get working directory
  pwd <- getwd()
  prefix <- 'tools/CrimeBBprocessR/R/'
  if (grepl('CrimeBBprocessR/R/', pwd)) {
    prefix <- './'
  }
  
  # load SVM model pre-trained by postTypeAuthorIntentAddresseeExperiments.R
  if (is.null(model)) {
    model <- readRDS(paste0(prefix, 'addressee_SVM.rds'))
  }
  # plus associated training data
  if (is.null(train.dtm)) {
    train.dtm <- readRDS(paste0(prefix, 'addressee_dtm.rds'))
  }
  # and label set (needed with e.g. XGBoost, not SVM)
  #if (is.null(labs)) {
  #  labs <- readRDS('authorIntent_labels.rds')
  #}

  df$addressee <- ''
  df$addresseeType <- ''
  for (r in 1:nrow(df)) {
    test.dtm <- data_prep(df[r,])
    xTest <- matrix_align(train.dtm, test.dtm)
    df$addresseeType[r] <- as.character(predict(model, xTest))

    # prediction post-processing
    if (df$addresseeType[r]=='threadOP') {
      df$addressee[r] <- df$threadOP[r]
    } else if (df$addresseeType[r]=='other') {
      if (df$hasCitation[r]) {  # if a citation
        df$addressee[r] <- df$citesUser[r]  # comes from initial_processing()
      } else if ((df$postNumber[r]==2) | (df$postNumber[r]==3)) {  # if 2nd or 3rd post, assume prev author is addressee
        subs <- subset(df, threadID==df$threadID[r])
        prevAuthor <- subs$author[which(subs$postID==df$postID[r])-1]  # previous row in subset for this thread
        df$addressee[r] <- prevAuthor
      }
    } else {
      if (df$firstPost[r]) {  # first post addressed to whole board
        df$addressee[r] <- 'bulletin_board'
      } else if ((!is.null(df$author[r])) & (!is.null(df$threadOP[r])) & (!is.na(df$author[r])) & (!is.na(df$threadOP[r]))) {  # check author/threadOP are not NA or NULL
        if (df$author[r]==df$threadOP[r]) {  # or if OP (later than 1st post), addressee is thread
          df$addressee[r] <- 'this_thread'
        } else {  # else assume OP
          df$addressee[r] <- df$threadOP[r]
        }
      } else {
        df$addressee[r] <- 'this_thread'
      }
    }
  }

  # return
  df
}
