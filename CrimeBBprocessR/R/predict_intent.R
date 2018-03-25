#' Predict Intent
#'
#' Predict the author's intent in writing a CrimeBB post.
#' Assumes at least the following columns: post, firstPost, sentiment (last 2 columns come from initial_processing() function).
#' Dependencies: tm, xgboost
#' @param df Input data frame object for processing, plus optional trained model, document-term matrix and list of labels used in model training.
#' @keywords author intent, sentiment
#' @export
#' @examples
#' predict_intent(my.df)

predict_intent <- function(df, model=NULL, train.dtm=NULL, labs=NULL) {

  # load XGB model pre-trained by postTypeAuthorIntentAddresseeExperiments.R
  if (is.null(model)) {
    model <- xgb.load('authorIntent_XGB.bin')
  }
  # plus associated training data
  if (is.null(train.dtm)) {
    train.dtm <- readRDS('authorIntent_dtm.rds')
  }
  # and label set (needed with e.g. XGBoost, not LM)
  if (is.null(labs)) {
    labs <- readRDS('authorIntent_labels.rds')
  }
  nLabels <- length(labs)

  # best guess at author's intent for each post
  df$intent <- ''
  for (r in 1:nrow(df)) {
    if (df$firstPost[r]) {  # first post is neutral
      df$intent[r] <- 'neutral'
    } else if (grepl('(violates|against)\\s+\\w+\\s+rules|wrong (section|forum)|can.*t post that|allowed here|t allowed|off(-| )topic|close this thread', df$post[r], perl=T, ignore.case=T)) {  # violates/against the/our rules, wrong section/forum, (not) (dis)allowed (here), off-topic, close this thread, cant post that here
      df$intent[r] <- 'moderate'
    } else if (grepl('retarded|idiot|you moron|this shit|skid|what the fuck|wtf', df$post[r], perl=T, ignore.case=T)) {  # this is retarded, idiotic, you moron, youre a fucking skid, what the fuck
      df$intent[r] <- 'aggression'
    } else if (grepl('gonna stop|please stop|this is bad|tell me you didn.*t|stopped reading|dubious|stolen|kidding me|gonna vomit|sucks balls|dwc|smilies/(sad|confused)', df$post[r], perl=T, ignore.case=T)) {  # are you gonna stop, please stop, this is bad, dubious, stolen, youre kidding me, im gonna vomit, this sucks balls, deal with caution, certain smilies
      df$intent[r] <- 'negative'
    } else if (grepl('haha|jaja|lo+l|\\blmao|glws|dope|check out|you (can|should) try|this is great|smilies/(roflmao|victoire|smile|tongue|haha)', df$post[r], perl=T, ignore.case=T)) {  # haha, jaja, lol, lmao, you can/should try, check out, this is dope, good luck with sale, certain smilies
      df$intent[r] <- 'positive'
    } else if (grepl('vouch', df$post[r], perl=T, ignore.case=T)) {
      df$intent[r] <- 'vouch'
    } else if (grepl('\\bthank(s|\\s+y*o*u|cheers ma)', df$post[r], perl=T, ignore.case=T)) {
      df$intent[r] <- 'gratitude'
    } else {
      if (grepl(':\\(', df$post[r], perl=T)) {
        df$intent[r] <- 'negative'
      } else if (grepl(':D', df$post[r], perl=T)) {
        df$intent[r] <- 'positive'
      } else {
        ## XGB classifier
        test.dtm <- data_prep(df[r,], xgb=T)
        xTest <- matrix_align(train.dtm, test.dtm)
        predict.vec <- predict(model, xTest)
        predict.df <- matrix(predict.vec, nrow=nLabels, ncol=length(predict.vec)/nLabels) %>% t() %>% data.frame() %>% mutate(max_prob=max.col(., 'last'))
        df$postType[r] <- as.character(labs[(predict.df$max_prob)-1])
      }
    }
  }
  ## append pm label
  if (grepl('\\bpm.*e*d*\\b|\\bhmu\\b|contact me\\b|skype|discord', df$post[r], perl=T, ignore.case=T)) {
      df$intent[r] <- paste0(df$intent[r], ',privatemessage')
  }

  # return
  df
}
