package hello

import org.springframework.stereotype.Controller

@Controller
class MainController {
    fun hello() {
        println("Hello World!")
    }
}