package hello

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController

@RestController
class MainController {
    @GetMapping("/hello")
    fun hello(@RequestParam name: String): String {
        return "Hello ${name}!"
    }
}
