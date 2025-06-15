package hello

import org.springframework.stereotype.Controller
import org.springframework.web.bind.annotation.*

@Controller
class MainController {
    @GetMapping("/hello")
    fun hello(@RequestParam name: String): String {
        return "Hello ${name}!"
    }
}
