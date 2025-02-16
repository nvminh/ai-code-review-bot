package com.reviewbot

import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/webhook")
class WebhookController {

    @PostMapping
    fun handleWebhook(@RequestBody payload: Map<String, Any>): String {
        val action = payload["action"] as String
        val pr = (payload["pull_request"] as Map<*, *>)["html_url"]
        println("PR Event Received: $action - $pr")
        return "Webhook received"
        xxx = yyy
    }
}

