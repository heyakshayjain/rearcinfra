resource "aws_ecr_repository" "sync_and_fetch" {
  name                 = "rearc-sync-and-fetch"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "analytics" {
  name                 = "rearc-analytics"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}
