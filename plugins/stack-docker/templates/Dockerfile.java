# syntax=docker/dockerfile:1
# Spring Boot (jar executável) com Maven wrapper e camadas do jar. Para Gradle: ./gradlew bootJar.
FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN --mount=type=cache,target=/root/.m2 ./mvnw -q dependency:go-offline
COPY src src
RUN --mount=type=cache,target=/root/.m2 ./mvnw -q package -DskipTests \
    && java -Djarmode=tools -jar target/*.jar extract --layers --launcher --destination /app

FROM eclipse-temurin:21-jre AS runtime
RUN useradd --uid 10001 app
WORKDIR /app
COPY --from=build --chown=app:app /app/dependencies/ ./
COPY --from=build --chown=app:app /app/spring-boot-loader/ ./
COPY --from=build --chown=app:app /app/snapshot-dependencies/ ./
COPY --from=build --chown=app:app /app/application/ ./
USER 10001
EXPOSE 8080
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75"
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
