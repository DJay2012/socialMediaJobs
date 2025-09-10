const axios = require('axios');
const cheerio = require('cheerio');

(async () => {
  try {
    // Fetch the HTML content from the website
    const { data } = await axios.get('https://www.anandabazar.com/');

    // Load the HTML into Cheerio
    const $ = cheerio.load(data);

    // Extract all the links
    const links = [];
    $('a').each((index, element) => {
      const link = $(element).attr('href');
      // Only add valid links (skip empty or undefined hrefs)
      if (link) {
        // If the link is relative, prepend the domain
        const fullLink = link.startsWith('http') ? link : `https://www.anandabazar.com${link}`;
        links.push(fullLink);
      }
    });

    // Print all the links
    console.log(links);

    // Optionally: Save the links to a file
    // const fs = require('fs');
    // fs.writeFileSync('links.json', JSON.stringify(links, null, 2));

  } catch (error) {
    console.error('Error fetching the page:', error);
  }
})();
