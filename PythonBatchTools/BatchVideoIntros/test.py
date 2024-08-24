import win32com.client
import os
import time

def create_fade_in_test_presentation(output_folder):
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    ppt.Visible = True

    try:
        presentation = ppt.Presentations.Add()
        
        # Add a slide with fade-in effect
        slide = presentation.Slides.Add(1, 1)  # Add a new slide
        shape = slide.Shapes.AddShape(1, 100, 100, 500, 100)  # Add a rectangle
        shape.TextFrame.TextRange.Text = "Fade-In Effect (Constant: 10)"
        
        sequence = slide.TimeLine.MainSequence
        try:
            effect = sequence.AddEffect(shape, 10, 0)  # 10 is the fade-in effect, 0 is trigger type "With Previous"
            effect.Timing.Duration = 2  # Set animation duration to 2 seconds
            print("Successfully added fade-in effect")
        except Exception as e:
            print(f"Failed to add fade-in effect. Error: {str(e)}")

        # Save the presentation with error handling and retry
        output_path = os.path.join(output_folder, "fade_in_test.pptx")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                presentation.SaveAs(output_path)
                print(f"Saved presentation: {output_path}")
                return True  # Successfully saved
            except Exception as save_error:
                print(f"Save attempt {attempt + 1} failed. Error: {str(save_error)}")
                if attempt < max_retries - 1:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("Failed to save after multiple attempts.")
                    return False  # Failed to save

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False
    finally:
        print("PowerPoint presentation is left open for your inspection.")
        print("Close PowerPoint manually when you're done.")

def main():
    # Create output folder
    output_folder = "animation_test_results"
    os.makedirs(output_folder, exist_ok=True)

    success = create_fade_in_test_presentation(output_folder)
    
    if success:
        print("Test completed successfully. You can find the saved presentation in the output folder.")
    else:
        print("Test completed with errors. Please check the console output for details.")

if __name__ == "__main__":
    main()