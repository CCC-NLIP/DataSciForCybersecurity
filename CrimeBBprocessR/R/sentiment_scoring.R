#' Sentiment Scoring
#'
#' Assigns sentiment score to CrimeBB posts
#' Assumes at least the following columns: postID, post, tokenCount (last column comes from initial_processing() function).
#' Depends on tidytext library
#' @param df Input data frame object for processing
#' @keywords sentiment analysis
#' @export
#' @examples
#' sentiment_scoring(my.df)

sentiment_scoring <- function(df) {

  # sentiment score for each post, normed by post length
  df$sentiment <- 0
  tibb.df <- data_frame(pid=df$postID, text=df$post)
  unnest.df <- tibb.df %>% unnest_tokens(word, text)
  senti.df <- unnest.df %>% inner_join(get_sentiments('afinn')) %>% group_by(postID=pid) %>% summarise(sentiment=sum(score)) %>% mutate(method='AFINN')
  for (r in 1:nrow(senti.df)) {
    pid <- senti.df$postID[r]
    sent <- senti.df$sentiment[r]
    df$sentiment[which(df$postID==pid)] <- sent / df$tokenCount[(which(df$postID==pid)[1])]
  }

  # return
  df
}
