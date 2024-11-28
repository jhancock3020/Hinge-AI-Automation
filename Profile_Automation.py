import adbutils
import xml.etree.ElementTree as ET
import time
import re
from PIL import Image
import os
from Image_Rating import rate_image
from chatgpt_api_test import chatgpt_input

# Needed to calculate how far the screen should scroll
screen_height = 0
screen_width = 0
x1 = 0
y1 = 0
x2 = 0
y2 = 0

# The over all number of images found and the overall sum of their ratings
profile_rating = 0
profile_images = 0

# Text extracted from profile and the chat gpt response to the extracted text
extracted_text = set()
chatgpt_response = ""

### GOING THROUGH ALL CHILD NODES OF SPECEFIC NODES ###

def go_through_first_view_factory_holder(device, xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    view_factory_holder = root.find(".//node[@class='androidx.compose.ui.viewinterop.ViewFactoryHolder']")
    click_first_subject_photo(device, view_factory_holder)

def go_through_view_factory_holder(device, xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for view_factory_holder in root.findall(".//node[@class='androidx.compose.ui.viewinterop.ViewFactoryHolder']"):
        extract_text(view_factory_holder)
        click_first_subject_photo(device, view_factory_holder)
        time.sleep(3)
        bounds = view_factory_holder.get('bounds')
        find_bounds(bounds)

def go_through_discover_liking_layout(device, xml_file):
    global chatgpt_response
    tree = ET.parse(xml_file)
    root = tree.getroot()
    cancel_button_bounds = ""
    liked_image_bounds = ""
    send_like_bounds = ""
    # Directly find the nodes with 'ViewFactoryHolder' class and extract text
    for discover_liking_layout in root.findall(".//node[@resource-id='co.hinge.app:id/discover_liking_layout']"):
        for node in discover_liking_layout.findall(".//node"):
            resource_id = node.attrib.get("resource-id", "")
            text = node.attrib.get("text", "")
            if chatgpt_response != "" and "/comment_composition_view" in resource_id:
                text_field_bounds = node.attrib.get("bounds", "")
                enter_text_into_field(device, text_field_bounds, chatgpt_response)
                time.sleep(2)
                press_escape_key(device)
                time.sleep(2)
            if chatgpt_response != "" and "Send Like" in text:
                send_like_bounds = node.attrib.get("bounds", "")
            elif chatgpt_response == "":
                if "motion_liked_content" in resource_id:
                    liked_image_bounds = node.attrib.get("bounds", "")
                if "cancel_button" in resource_id:
                    cancel_button_bounds = node.attrib.get("bounds", "")

    if send_like_bounds != "" and chatgpt_response != "":
        click_bounds(device, send_like_bounds)
        return
    if liked_image_bounds != "" and chatgpt_response == "":
        take_screenshot_of_element(device, liked_image_bounds)
        rate_current_screenshot()
    if cancel_button_bounds != "" and chatgpt_response == "":
        click_bounds(device, cancel_button_bounds)
    return
### CLICKING SPECEFIC BUTTONS ###

def press_escape_key(device):
    device.shell("input keyevent 4")  # Key event 4 corresponds to the ESC key

def find_and_click_no_button(device, xml_file):
    """
    Extract unique text content from nodes under 'ViewFactoryHolder'.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    no_button = root.find(".//node[@resource-id='co.hinge.app:id/no_button']")
    no_button_bounds = no_button.get('bounds')
    click_bounds(device, no_button_bounds)

def click_first_subject_photo(device, view_factory_holder):
    is_photo = False
    has_like_button = False
    like_button_bounds = ""
    for node in view_factory_holder.findall(".//node"):
        resource_id = node.attrib.get("resource-id", "")
        #print(resource_id)
        # Use regular expression to extract the numbers
        if 'subject_photo' in resource_id or 'video_rounded_frame' in resource_id :
            is_photo = True
        if 'like_button' in resource_id:
            has_like_button = True
            like_button_bounds = node.attrib.get("bounds", "")
        if is_photo and has_like_button:
            click_bounds(device, like_button_bounds)
            time.sleep(2)
            image_xml_file = dump_ui_image_hierarchy(device)
            go_through_discover_liking_layout(device,image_xml_file)

### TEXT BASED METHODS ###
         
def extract_text(view_factory_holder):
    global extracted_text
    for node in view_factory_holder.findall(".//node"):
        text = node.attrib.get("text", "")
        if text and text not in extracted_text:
            extracted_text.add(text)  # Add text to the set
            print(f"Unique text found: {text}")

def enter_text_into_field(device, bounds, text):
    click_bounds(device, bounds)
    device.shell(f'input text "{text}"')
    #print(f"Entered text: {text}")
    
### BOUNDS AND SCROLL CALCULATIONS RELATED METHODS ###
           
def find_bounds(bounds):
    global x1, y1, x2, y2
    matches = re.findall(r'(\d+)', bounds)
    # Convert the matches to integers and assign them to individual variables
    x1, y1, x2, y2 = map(int, matches)

def click_bounds(device, bounds):
    # Calculate the center position for the click
    bounds = [int(coord) for coord in bounds.strip("[]").replace("][", ",").split(",")]
    x = (bounds[0] + bounds[2]) // 2
    y = (bounds[1] + bounds[3]) // 2

     # Perform the click
    device.shell(f"input tap {x} {y}")
    #print(f"Clicked on like button at ({x}, {y}) with bounds {bounds}")

def scroll_calculations(device):
    scroll_distance = abs(int(x1) - int(screen_height))
    #print( str(x1) + " % " + str(screen_height) + " " + str(scroll_distance))
    if scroll_distance > 0:  # Only scroll if the node is below the screen
        #print(f"Scrolling {scroll_distance} pixels up.")
        # Perform a swipe scroll upwards to bring the node just above the top
        device.shell(f"input swipe 500 1500 500 {1500 - scroll_distance}")  # Adjust coordinates as necessary


def get_screen_size(device):
    global screen_height, screen_width
    # Get the screen resolution using 'wm size'
    screen_size = device.shell("wm size")
    resolution = screen_size.strip().split(":")[1].strip()
    screen_width, screen_height = resolution.split("x")


### DUMP CURRENT UI INFO FROM XML FILE ###
    
def dump_ui_hierarchy(device):

    xml_path = "ui_dump.xml"
    device.shell("uiautomator dump /sdcard/ui_dump.xml")
    device.sync.pull("/sdcard/ui_dump.xml", xml_path)
    return xml_path

def dump_ui_image_hierarchy(device):

    xml_path = "ui_image_dump.xml"
    device.shell("uiautomator dump /sdcard/ui_image_dump.xml")
    device.sync.pull("/sdcard/ui_image_dump.xml", xml_path)
    return xml_path

### SCREENSHOTS AND RATING SCREENSHOTS ###

def take_screenshot_of_element(device, bounds):
    try:
        # Take a screenshot and save it to the device
        screenshot_path = "/sdcard/screenshot.png"
        local_screenshot = "screenshot.png"
        device.shell(f"screencap -p {screenshot_path}")

        # Pull the screenshot to your local machine
        device.sync.pull(screenshot_path, local_screenshot)

        # Extract coordinates from the bounds string
        coords = re.findall(r"\d+", bounds)
        if len(coords) != 4:
            print(f"Invalid bounds string: {bounds_string}")
            return
        x1, y1, x2, y2 = map(int, coords)

        # Open the screenshot and crop it
        with Image.open(local_screenshot) as img:
            # Crop the image using the bounds (x1, y1, x2, y2)
            cropped_img = img.crop((x1, y1, x2, y2))

            # Save the cropped image
            cropped_img.save("cropped_element.png")
            #print(f"Cropped image saved as 'cropped_element.png'")

        # Optional: Clean up the local screenshot file
        os.remove(local_screenshot)

    except Exception as e:
        print(f"Error in take_screenshot_of_element: {e}")

def rate_current_screenshot():
    global profile_rating, profile_images
    current_rating = rate_image()
    print(str(current_rating))
    if current_rating != -1:
        profile_rating += current_rating
        profile_images += 1
        #print("profile_rating so far: " + str(profile_rating) + " " + str(profile_images))


### SWIPING LEFT OR RIGHT DEPENDING ON PROFILE ###

def profile_swipe_choice(device, xml_file):
    global profile_rating, profile_images, extracted_text, chatgpt_response
    banned_words = ["evil"]
    rating_threshold = 3
    print("Overall profile rating " + str(profile_rating) + " / " + str(profile_images))
    if(profile_images > 0):
        final_profile_rating = profile_rating / profile_images
        if final_profile_rating < rating_threshold or any(banned_word in extracted_text for banned_word in banned_words):
            #print("DISLIKED")
            find_and_click_no_button(device, xml_file)
        else:
            #print("LIKED")
            chatgpt_response = chatgpt_input(str(extracted_text))
            scroll_up_to_top_of_profile(device)
            xml_file = dump_ui_hierarchy(device)
            go_through_first_view_factory_holder(device, xml_file)
    print("Profile Complete!")
    return

### SCROLLING DOWN AND UP ###
      
def scroll_up_to_top_of_profile(device):

    last_dump = ""

    while True:
        # Dump the current UI hierarchy to a file (in XML format)
        device.shell("uiautomator dump /sdcard/ui_dump.xml")
        
        # Pull the XML dump from BlueStacks to your local machine
        device.sync.pull("/sdcard/ui_dump.xml", "ui_dump.xml")
        
        # Read the current UI hierarchy as a string
        with open("ui_dump.xml", "r", encoding="utf-8") as file:
            current_dump = file.read()
        
        # Check if the current dump is the same as the last one (no more to scroll)
        if current_dump == last_dump:
            #print("Reached the top of the conversation.")
            break

        # Update last dump to detect when scrolling has no new results
        last_dump = current_dump

        # Scroll up the chat to load previous content
        device.shell("input swipe 500 200 500 1000")  # Adjust the swipe values as needed
        time.sleep(2)  # Add a delay to allow the UI to update

def scroll_and_check(device):
    """
    Scrolls down and checks for UI changes.
    """
    last_ui_dump = ""
    get_screen_size(device)
    while True:
        print("Dumping UI hierarchy...")
        xml_file = dump_ui_hierarchy(device)
       # print("Processing UI dump...")
        # Read the current UI hierarchy as a string
        with open(xml_file, "r", encoding="utf-8") as file:
            ui_dump = file.read()
        
        if ui_dump == last_ui_dump:
            #print("No changes in UI. Ending the app.")
            profile_swipe_choice(device, xml_file)
            break
        else:
            #extracted_text = extract_text_from_view_factory_holder(xml_file)
            go_through_view_factory_holder(device, xml_file)
            last_ui_dump = ui_dump
            print("Scrolling down...")
            scroll_calculations(device)
            #device.shell("input swipe 500 1500 500 1000")  # Adjusted swipe coordinates for a smaller scroll

            # Wait a few seconds before checking again
            time.sleep(3)

### MAIN METHOD ###

if __name__ == "__main__":
    # Initialize ADB client and connect to the device
    adb = adbutils.AdbClient(host="127.0.0.1", port=5037)
    adb.connect("127.0.0.1:5555")
    device = adb.device("127.0.0.1:5555")

    if device is None:
        print("Error: Device is not connected.")
        exit(1)
    scroll_and_check(device)
