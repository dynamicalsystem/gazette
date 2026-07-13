loop: 05-ci-ghcr
closed: 2026-07-07
outcome: met -- merge to main publishes a multi-arch GHCR image; legacy deploy deleted

Key result: release.yml builds linux/amd64+arm64 and pushes
ghcr.io/dynamicalsystem/gazette:latest (+sha); docker-compose.yml / deploy.sh /
build-and-push.yml removed; README Deploy section rewritten; main on origin.
Verified 2026-07-07: CI green on 5da069b, GHCR tags latest + 2 sha, v0.1.5.
Outcomes O1-O4 met.
Successors: 06-service-skeleton, 07 (quadlet pulls the image).
