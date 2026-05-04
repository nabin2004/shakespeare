# Runtime image for WIDOCO (https://github.com/dgarijo/Widoco) — generates HTML + WebVOWL from OWL.
FROM eclipse-temurin:17-jre-jammy

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    libfreetype6 \
    fontconfig \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG WIDOCO_VERSION=1.4.25
ARG WIDOCO_JAR=widoco-1.4.25-jar-with-dependencies_JDK-17.jar

RUN wget -q -O /opt/widoco.jar \
    "https://github.com/dgarijo/Widoco/releases/download/v${WIDOCO_VERSION}/${WIDOCO_JAR}"

WORKDIR /work

ENTRYPOINT ["java", "-jar", "/opt/widoco.jar"]
