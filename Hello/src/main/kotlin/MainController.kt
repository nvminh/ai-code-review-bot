package hello

import org.springframework.stereotype.Controller

@Controller
class MainController {
    @GetMapping
    fun hello() {
        println("Hello World!")
    }
}
