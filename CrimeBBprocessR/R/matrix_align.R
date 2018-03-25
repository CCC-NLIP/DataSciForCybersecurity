#' Align Document-Term Matrices
#'
#' Align two data frames where 1st df was used to train stat.model and 2nd df is target data
#' Returns matrix with columns ordered alphabetically by column header
#' Assumes the following columns: post
#' @param df Two data frames
#' @keywords preprocessing, machine learning
#' @export
#' @examples
#' matrix_align(my.df1, my.df2)

matrix_align <- function(df1, df2) {

  # empty matrix length of mtx2
  new.mtx <- matrix(0)
  new.mtx <- do.call('rbind', replicate(nrow(mtx2), new.mtx, simplify=F))  # n.rows
  # populate with zero columns for mtx1 cols not in mtx2
  new.mtx <- do.call('cbind', replicate(sum(!colnames(mtx1) %in% colnames(mtx2)), new.mtx, simplify=F))
  mtx1.not.mtx2 <- which(!colnames(mtx1) %in% colnames(mtx2))
  # keep any relevant cols from mtx2, add missing cols from mtx1
  if (length(mtx1.not.mtx2)>0) {
    colnames(new.mtx) <- colnames(mtx1)[mtx1.not.mtx2]
    new.mtx <- cbind(new.mtx, mtx2)
  } else {
    new.mtx <- mtx2
  }
  # alpha sort column headers
  if (nrow(mtx2)==1) {  # transpose first
    new.mtx <- t(as.matrix(new.mtx[, order(colnames(new.mtx))]))
  } else {
    new.mtx <- new.mtx[, order(colnames(new.mtx))]
  }
  # return
  new.mtx
}
