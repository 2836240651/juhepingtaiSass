FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY app.jar /app/app.jar
RUN mkdir -p /data
ENV SPRING_PROFILES_ACTIVE=prod
ENV CROSSHUB_DB_PATH=/data/crosshub.db
EXPOSE 18080
ENTRYPOINT ["java", "-jar", "/app/app.jar", "--server.port=18080"]
