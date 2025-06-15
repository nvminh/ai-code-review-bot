import hello.MainController
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.get

@WebMvcTest(MainController::class)
class MainControllerTest(@Autowired val mockMvc: MockMvc) {

    @Test
    fun `should return greeting with name`() {
        mockMvc.get("/hello") {
            param("name", "Minh")
        }
            .andExpect {
                status { isOk() }
                content { string("Hello Minh!") }
            }
    }
}