% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/sentiment_scoring.R
\name{sentiment_scoring}
\alias{sentiment_scoring}
\title{Sentiment Scoring}
\usage{
sentiment_scoring(df)
}
\arguments{
\item{df}{Input data frame object for processing}
}
\description{
Assigns sentiment score to CrimeBB posts
Assumes at least the following columns: postID, post, tokenCount (last column comes from initial_processing() function).
Depends on tidytext library
}
\examples{
sentiment_scoring(my.df)
}
\keyword{analysis}
\keyword{sentiment}
