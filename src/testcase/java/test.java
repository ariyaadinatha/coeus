import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.io.File;
import java.nio.file.Path;
import java.nio.file.Paths;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.jfinal.core.Controller;

public class FilePathInjection extends Controller {
	private static final String BASE_PATH = "/pages";

	// BAD: Upload file to user specified path without validation
	public void uploadFile() throws IOException {
		String savePath = getPara("dir");
		File file = getFile("fileParam").getFile();
		String finalFilePath = BASE_PATH + savePath;

		FileInputStream fis = new FileInputStream(file);
		FileOutputStream fos = new FileOutputStream(finalFilePath);
		int i = 0;

		do {
			byte[] buf = new byte[1024];
			i = fis.read(buf);
			fos.write(buf);
		} while (i != -1);
		
		fis.close();
		fos.close();
	}
}
