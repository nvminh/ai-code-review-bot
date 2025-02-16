package com.reviewbot

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class ReviewBotApp

fun main(args: Array<String>) {
    runApplication<ReviewBotApp>(*args)
}

